#!/usr/bin/env python
"""Tries to follow a rectangular track around the course."""

import signal
from time import sleep
import comm.serial_interface as comm
from vision.util import Enum, log_str
from vision import vision
import logging.config
from mapping import pickler
import pprint as pp
from collections import namedtuple
from math import sqrt, hypot, atan2, degrees, radians, sin, cos, pi
from multiprocessing import Process, Manager, Queue

default_speed = 300
waypoints_file = "mapping/waypoints.pkl"
#inchesToMeters = 0.0254

Point = namedtuple('Point', ['x', 'y'])
Offset = namedtuple('Offset', ['x', 'y'])  # slightly different in meaning from Point, can be negative
Size = namedtuple('Size', ['width', 'height'])

#map_size = Size(97, 73)  # (width, height) of entire course, inches
map_size = Size(97, 49)  # exterior (width, height) of the lower part, inches
map_bounds = (Point(0.75, 0.75), Point(96.25, 48.25)) # interior bounds: ((x0, y0), (x1, y1)), inches
# TODO check map bounds are correct

class Node:
  """A map location encapsulated as a graph node."""
  def __init__(self, name, loc, theta=0.0):
    self.name = name
    self.loc = loc  # (x, y), location on map, inches
    self.theta = theta  # *preferred* orientation, radians; NOTE must be a multiple of pi/2 to make the rectilinear calculations work
    
    # Compute expected distances from the edges (in inches): north, south, east, west
    self.dists = dict(
      north = map_bounds[1].y - self.loc.y,
      south = self.loc.y - map_bounds[0].y,
      east = map_bounds[1].x - self.loc.x,
      west = self.loc.x - map_bounds[0].x)
    # TODO compensate for bot width, height and center offset
  
  def __str__(self):
    return "<Node {self.name}; loc: {self.loc}, theta: {self.theta}, dists: {self.dists}>".format(self=self)
  
  def dump(self):
    return "Node {self.name} {self.loc.x} {self.loc.y} {self.theta} {self.dists[north]} {self.dists[south]} {self.dists[east]} {self.dists[west]}".format(self=self)
  
  @classmethod
  def dumpHeader(cls):
    return "Node name x y theta north south east west"


class Edge:
  """A directed edge from one node to another."""
  def __init__(self, fromNode, toNode):
    self.fromNode = fromNode
    self.toNode = toNode
    # TODO add strategy to navigate between these two nodes


class Graph:
  """A graph of map locations (nodes) and ways to traverse between then (edges)."""
  def __init__(self, nodes=dict(), edges=dict()):
    self.nodes = nodes
    self.edges = edges


class Bot:
  """Encapsulates bot's current state on the map."""
  def __init__(self, loc, heading=0.0):
    self.loc = loc  # (x, y), location on map, inches
    self.heading = heading  # current orientation, radians
  
  def __str__(self):
    return "<Bot loc: {self.loc}, heading: {self.heading}>".format(self=self)


class TrackFollower:
  """A bot control that makes it move along a pre-specified track."""
  def __init__(self, sc, logger=None):
    self.sc = sc
    self.logger = None
    if logger is not None:
      self.logger = logger
    else:
      logging.config.fileConfig('logging.conf')
      self.logger = logging.getLogger('track_follower')
    self.debug = True
    
    # Read waypoints from file
    self.waypoints = pickler.unpickle_waypoints(waypoints_file)
    self.logd("__init__()", "Loaded waypoints")
    #pp.pprint(self.waypoints)  # [debug]
    
    # TODO Create nodes (waypoints) and edges using graph methods to simplify things
    self.graph = Graph()
    self.graph.nodes['start'] = Node('start', Point(self.waypoints['start'][1][0], self.waypoints['start'][1][1]), self.waypoints['start'][2])
    self.graph.nodes['alpha'] = Node('alpha', Point(15, 12), 0)  # first point to go to
    self.graph.nodes['land'] = Node('land', Point(39.5, 12), 0)  # point near beginning of land
    self.graph.nodes['beta'] = Node('beta', Point(64, 12), pi/2)  # point near one end of land and beginning of ramp
    self.graph.nodes['east_off'] = Node('east_off', Point(64, 20), pi/2)  # point beside start of ramp when we should switch off east sensor
    self.graph.nodes['celta'] = Node('celta', Point(64, 34), pi)  # point beside ramp
    self.graph.nodes['pickup'] = Node('pickup', Point(58, 34), pi)  # point near start of pickup
    self.graph.nodes['delta'] = Node('delta', Point(12, 34), pi)  # point past end of pickup
    self.graph.nodes['sea'] = Node('sea', Point(12, 34), 3*pi/2)  # point near start of sea
    self.graph.nodes['eps'] = Node('eps', Point(12, 12), 0)  # point past end of sea
    
    self.graph.edges[('start', 'alpha')] = Edge(self.graph.nodes['start'], self.graph.nodes['alpha'])
    self.graph.edges[('alpha', 'land')] = Edge(self.graph.nodes['alpha'], self.graph.nodes['land'])
    self.graph.edges[('land', 'beta')] = Edge(self.graph.nodes['land'], self.graph.nodes['beta'])
    self.graph.edges[('beta', 'east_off')] = Edge(self.graph.nodes['beta'], self.graph.nodes['east_off'])
    self.graph.edges[('east_off', 'celta')] = Edge(self.graph.nodes['east_off'], self.graph.nodes['celta'])
    self.graph.edges[('celta', 'pickup')] = Edge(self.graph.nodes['celta'], self.graph.nodes['pickup'])
    self.graph.edges[('pickup', 'delta')] = Edge(self.graph.nodes['pickup'], self.graph.nodes['delta'])
    self.graph.edges[('delta', 'sea')] = Edge(self.graph.nodes['delta'], self.graph.nodes['sea'])
    self.graph.edges[('sea', 'eps')] = Edge(self.graph.nodes['sea'], self.graph.nodes['eps'])
    self.graph.edges[('eps', 'alpha')] = Edge(self.graph.nodes['eps'], self.graph.nodes['alpha'])
    
    
    self.init_path = [self.graph.edges[('start', 'alpha')]]
    
    self.path = [
      self.graph.edges[('alpha', 'land')],
      self.graph.edges[('land', 'beta')],
      self.graph.edges[('beta', 'east_off')],
      self.graph.edges[('east_off', 'celta')],
      self.graph.edges[('celta', 'pickup')],
      self.graph.edges[('pickup', 'delta')],
      self.graph.edges[('delta', 'sea')],
      self.graph.edges[('sea', 'eps')],
      self.graph.edges[('eps', 'alpha')]
      ]
    
    # Report entire path
    self.logd("__init__()", "Path:")
    print Node.dumpHeader()
    for edge in self.path:
      print edge.fromNode.dump()
    if edge is not None:
      print edge.toNode.dump()
    
    # Initialize bot at start location
    self.bot = Bot(self.graph.nodes['start'].loc)
  
  def run(self):
    # Units:- angle: 10ths of degree, distance: encoder counts (1000 ~= 6 in.), speed: PID value (200-1000)
    
    # * Traverse through the list of nodes in initial path to get to alpha
    for edge in self.init_path:
      self.traverse(edge)
    
    # * Traverse through the list of nodes in path
    for edge in self.path:
      self.traverse(edge)
    
    # * Turn to the orientation of the last edge's toNode
    if edge is not None:
      self.turn(edge.toNode.theta)
    
    self.stop()
  
  def traverse(self, edge):
    # TODO move from edge.fromNode to edge.toNode, ensuring bot sensors indicate expected values
    self.logd("traverse", "Moving from {from} to {to}...".format(from=edge.fromNode.name, to=edge.toNode.name))
    self.move(edge.fromNode.loc, edge.toNode.loc)
  
  def move(self, fromPoint, toPoint, speed=default_speed):
    self.logd("move", "Bot: {}".format(self.bot))  # report current state
    
    # * Compute angle and distance
    delta = Offset(toPoint.x - fromPoint.x, toPoint.y - fromPoint.y)
    distance_inches = hypot(delta.x, delta.y)
    #angle_radians = atan2(delta.y, delta.x) % (2 * pi)  # absolute angle
    angle_radians = (atan2(delta.y, delta.x) - self.bot.heading) % (2 * pi)  # relative angle
    
    distance = int(distance_inches * (1633 / 9.89))
    angle = int(degrees(angle_radians)) * 10
    
    # * Turn in the desired direction
    # ** Option 1: Absolute
    '''
    self.logd("move", "Command: botTurnAbs({angle})".format(angle=angle))
    actual_heading = self.sc.botTurnAbs(angle)
    self.logd("move", "Response: heading = {heading}".format(heading=actual_heading))
    '''
    # ** Option 2: Relative
    # * Turn in the desired direction (absolute)
    self.logd("move", "Command: botTurnRel({angle})".format(angle=angle))
    actual_heading_rel = self.sc.botTurnRel(angle)
    self.logd("move", "Response: heading = {heading}".format(heading=actual_heading_rel))
    
    # * Update bot heading
    #self.bot.heading = radians(actual_heading / 10.0)  # absolute angle
    self.bot.heading = self.bot.heading + radians(actual_heading_rel / 10.0)  # relative angle
    self.logd("move", "Bot: {}".format(self.bot))
    
    # * Move in a straight line while maintaining known heading (absolute)
    # ** Option 1: Use botSet()
    '''
    self.logd("move", "Command: botSet({distance}, {angle}, {speed})".format(distance=distance, angle=angle, speed=speed))
    actual_distance, actual_heading = self.sc.botSet(distance, angle, speed)
    self.logd("move", "Response: distance = {distance}, heading = {heading}".format(distance=actual_distance, heading=actual_heading))
    '''
    # ** Option 2: Use botMove()
    self.logd("move", "Command: botMove({distance}, {speed})".format(distance=distance, speed=speed))
    actual_distance = self.sc.botMove(distance, speed)
    self.logd("move", "Response: distance = {distance}".format(distance=actual_distance))
    
    #TODO correct heading to closest multiple of pi/2?
    
    # * Update bot loc and heading
    actual_distance_inches = actual_distance * (9.89 / 1633)
    self.bot.loc = Point(self.bot.loc.x + actual_distance_inches * cos(self.bot.heading), self.bot.loc.y + actual_distance_inches * sin(self.bot.heading))
    #self.bot.heading = radians(actual_heading / 10.0)  # only needed if botSet() was used
    self.logd("move", "Bot: {}".format(self.bot))
  
  def turn(self, angle_radians):
    # * Compute angle
    angle = int(degrees(angle_radians)) * 10
    
    # * Turn in the desired direction (absolute)
    self.logd("turn", "Command: botTurnAbs({angle})".format(angle=angle))
    actual_heading = self.sc.botTurnAbs(angle)
    self.logd("turn", "Response: heading = {heading}".format(heading=actual_heading))
    
    # * Update bot heading
    self.bot.heading = radians(actual_heading / 10.0)
    self.logd("move", "Bot: {}".format(self.bot))
    
  def stop(self):
      self.logd("stop", "Command: botStop()")
      stop_result = self.sc.botStop()
      self.logd("stop", "Response: result = {result}".format(result=stop_result))
  
  def loge(self, func, msg):
    outStr = log_str(self, func, msg)
    print outStr
    if self.logger is not None:
      self.logger.error(outStr)
  
  def logi(self, func, msg):
    #log(self, func, msg)
    outStr = log_str(self, func, msg)
    print outStr
    if self.logger is not None:
      self.logger.info(outStr)
  
  def logd(self, func, msg):
    #if self.debug:
    #  log(self, func, msg)
    outStr = log_str(self, func, msg)
    if self.debug:  # only used to filter messages to stdout, all messages are sent to logger if available
      print outStr
    if self.logger is not None:
      self.logger.debug(outStr)


def main():
  # Build shared data structures
  print "main(): Creating shared data structures..."
  manager = Manager()
  bot_loc = manager.dict(x=-1, y=-1, theta=0.0, dirty=False)  # manage bot loc in track follower
  blobs = manager.list()  # for communication between vision and planner
  blocks = manager.dict()
  zones = manager.dict()
  corners = manager.list()
  bot_state = manager.dict(nav_type=None, action_type=None, naving=False) #nav_type is "micro" or "macro"
  
  # Set shared parameters and flags
  bot_state['cv_offsetDetect'] = False
  bot_state['cv_lineTrack'] = True
  
  # Serial interface and command
  print "main(): Creating SerialInterface process..."
  si = comm.SerialInterface(timeout=1.0)
  si.start()
  sc = comm.SerialCommand(si.commands, si.responses)
  
  # Instantiate track follower
  trackFollower = TrackFollower(sc)
  waypoints = trackFollower.waypoints  # TODO this is a hack; fold main() into TrackFollower.run()
  
  # Start vision process, pass it shared data
  scVision = comm.SerialCommand(si.commands, si.responses)
  options = dict(filename=None, gui=False, debug=True)
  pVision = Process(target=vision.run, args=(bot_loc, blobs, blocks, zones, corners, waypoints, scVision, bot_state, options))
  pVision.start()
  
  # Zero compass heading
  sc.compassReset()
  
  # Set signal handlers
  live = True
  def handleSignal(signum, frame):
    if signum == signal.SIGTERM or signum == signal.SIGINT:
      print "main.handleSignal(): Termination signal ({0}); stopping comm loop...".format(signum)
    else:
      print "main.handleSignal(): Unknown signal ({0}); stopping comm loop anyways...".format(signum)
    #si.quit()
    live = False
  
  signal.signal(signal.SIGTERM, handleSignal)
  signal.signal(signal.SIGINT, handleSignal)
  
  # Start track follower
  print "Ready..."
  sleep(1)  # delay to let button presser move back hand
  print "Go!"
  trackFollower.run()
  
  # Reset signal handlers to default behavior
  signal.signal(signal.SIGTERM, signal.SIG_DFL)
  signal.signal(signal.SIGINT, signal.SIG_DFL)
  
  # Wait for child processes to join
  bot_state['die'] = True
  pVision.join()
  
  sc.quit()
  si.join()
  print "main(): Done."


if __name__ == "__main__":
  main()