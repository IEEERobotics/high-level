#!/usr/bin/env python
"""Tries to follow a rectangular track around the course."""

import signal
from time import sleep
import comm.serial_interface as comm
from vision.util import Enum, log_str
import logging.config
from mapping import pickler
import pprint as pp
from collections import namedtuple
from math import sqrt, hypot

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
  def __init__(self, loc, theta=0.0):
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
    return "<Node loc: {self.loc}, theta: {self.theta}, dists: {self.dists}>".format(self=self)
  
  #@classmethod
  #def getNodeInches(loc_inches, theta):
  #  return None


class Edge:
  """A directed edge from one node to another."""
  def __init__(self, fromNode, toNode):
    self.fromNode = fromNode
    self.toNode = toNode
    # TODO add strategy to navigate between these two nodes


class Graph:
  """A graph of map locations (nodes) and ways to traverse between then (edges)."""
  def __init__(self, nodes=list(), edges=list()):
    self.nodes = nodes
    self.edges = edges


class Bot:
  """Encapsulates bot's current state on the map."""
  def __init__(self, loc, theta=0.0):
    self.loc = loc  # (x, y), location on map, inches
    self.theta = theta  # current orientation, radians


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
    
    # TODO Create nodes (waypoints) and edges
    waypoints = pickler.unpickle_waypoints(waypoints_file)
    self.logd("__init__()", "Loaded waypoints")
    #pp.pprint(waypoints)  # [debug]
    
    startNode = Node(Point(waypoints['start'][1][0], waypoints['start'][1][1]), waypoints['start'][2])
    self.logd("__init__()", "start: {0}".format(startNode))  # [debug]
  
  def run(self): 
    # Units:- angle: 10ths of degree, distance: encoder counts (1000 ~= 6 in.), speed: PID value (200-1000)
    
    # TODO do your thing
    return
  
  def move(self, fromPoint, toPoint):
    # * Compute angle and distance
    delta = Offset(toPoint.x - fromPoint.x, toPoint.y - fromPoint.y)
    distance = sqrt(delta.x**2 + delta.y**2)
    angle = hypot(delta.y, delta.x)
    
    # * Turn in the desired direction (absolute)
    self.logd("move", "Command: botTurnAbs({angle})".format(angle=angle))
    actual_heading = self.sc.botTurnAbs(angle)
    self.logd("move", "Response: heading = {heading}".format(heading=actual_heading))
    
    # * Move in a straight line while maintaining known heading (absolute)
    self.logd("move", "Command: botSet({distance}, {angle}, {speed})".format(distance=distance, angle=angle, speed=speed))
    actual_distance, actual_heading = self.sc.botSet(distance, angle, speed)
    self.logd("move", "Response: distance = {distance}, heading = {heading}".format(distance=actual_distance, heading=actual_heading))
    
    # * Turn to destination's desired heading (TODO simply correct heading to closest multiple of pi/2?)
    self.logd("move", "Command: botTurnAbs({angle})".format(angle=angle))
    actual_heading = self.sc.botTurnAbs(angle)
    self.logd("move", "Response: heading = {heading}".format(heading=actual_heading))
    
    # * Stop
    self.logd("move", "Command: botStop()")
    stop_result = self.sc.botStop()
    self.logd("move", "Response: result = {result}".format(result=stop_result))
  
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
  # Serial interface and command
  print "main(): Creating SerialInterface process..."
  si = comm.SerialInterface(timeout=1.0)
  si.start()
  sc = comm.SerialCommand(si.commands, si.responses)
  
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
  
  # Zero compass heading
  sc.compassReset()
  
  # Instantiate track follower and start it
  trackFollower = TrackFollower(sc)
  print "Ready..."
  sleep(2)  # delay to let button presser move back hand
  print "Go!"
  trackFollower.run()
  
  # Reset signal handlers to default behavior
  signal.signal(signal.SIGTERM, signal.SIG_DFL)
  signal.signal(signal.SIGINT, signal.SIG_DFL)
  
  sc.quit()
  si.join()
  print "main(): Done."


if __name__ == "__main__":
  main()