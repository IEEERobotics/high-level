#!/usr/bin/python

from numpy import random, pi, zeros

import robot, particles, map, pose
import time  # sleep

import std_sensors, std_noise

import sys, os
sys.path.append('..')
import mapping.map_class
sys.modules['map_class'] = mapping.map_class  # deal with the fact we pickled a module in another dir
import mapping.pickler
import logging.config

def run( bot_loc, zones, map_properties, course_map, waypoints, ipc_channel, bot_state, logger=None ):

  logger.debug("Localizer entry point: run()")

  start_pose = pose.Pose(bot_loc["x"],bot_loc["y"],bot_loc["theta"])
  ideal = robot.SimRobot(start_pose, std_sensors.offset_str)
  logger.debug("Initial pose: %s" % start_pose)

  themap = map.Map.from_map_class(course_map, logger = logger)
  logger.debug("Map dimensions: %s" % themap)
  last_zone_change = 0

  if not ipc_channel:
    logging.debug("Using Fake_IPC queue")
    ipc_channel = Fake_IPC(start_pose, themap, delay = 1.0, logger = logger)

  #localizer = DumbLocalizer(start_pose)
  localizer = particles.ParticleLocalizer(std_sensors.offset_str, std_noise.noise_params, themap, 50, start_pose, logger = logger)

  while True:
    msg = ipc_channel.get()
    logger.debug("From qNav (raw): %s" % msg)
    if type(msg) == str and msg == 'die':
      logger.debug("Received die signal, exiting...")
      exit(0)
    
    turn, move = msg['dTheta'], msg['dXY']
    logger.debug("Turn: %+0.2f, Move: %0.2f" % (turn, move))

    sensorData = msg['sensorData']
    logger.debug( "SensorData: %s" % sensorData)
    # pull out ultrasonic data
    sensors = {}
    for key,val in sensorData['ultrasonic'].items():
      sensors[key] = val
    logger.debug( "Sensors-only dict: %s" % sensors)

    # update map if zone status has changed
    zone_change = bot_state['zone_change']
    logger.debug("Checking for block zone change (last update: %d, now: %d)" % (last_zone_change, zone_change))
    if zone_change > last_zone_change:  
      logger.debug("Map zones are behind, updating")
      logger.debug("Current zones dict: %s" % zones)
      for zone, state in zones.items():
        if state == True:
          logger.debug("Wall-filling location: %s" % zone)
          #course_map.fillLoc(waypoints, zone, {'desc':8})
          themap.map_obj.fillLoc(waypoints, zone, {'desc':8})
        else:
          themap.map_obj.fillLoc(waypoints, zone, {'desc':0})
      themap.update()
      last_zone_change = zone_change

    ideal.move(turn, move)
    localizer.move(turn, move)
    logger.debug( "Ideal pose: %s" % ideal.pose)
    localizer.update(sensors)
    guess = localizer.guess()
    logger.debug("Guess pose: %s" %  guess)

    bot_loc['x'] = guess.x
    bot_loc['y'] = guess.y
    bot_loc['theta'] = guess.theta
    bot_loc['dirty'] = False

#################################
class Fake_IPC(object):

  ''' sensorData: 
        {'accel': {'x': 0, 'y': 0, 'z': 980},
         'heading': 0.0,
         'id': 0,
         'msg': 'This is fake',
         'result': True,
         'ultrasonic': {'back': 1.3385833999999999,
                        'front': 1.3385833999999999,
                        'left': 1.3385833999999999,
                        'right': 1.3385833999999999}}
  '''
  def __init__(self, start_pose, map_data, delay = 0.0, logger = None):
    self.delay = delay
    self.logger = logger
    self.map = map_data
    self.simbot = robot.SimRobot(pose = start_pose, sensors = std_sensors.offset_str, 
                            noise_params = std_noise.noise_params)
    logger.debug( "Fake_IPC simbot initial pose: %s" % self.simbot)
    sensed = self.simbot.sense(self.map)
    logger.debug( "Simbot initial sense: %s" % sensed)

  def get(self):
    self.logger.debug("SimBot pose: %s" % self.simbot.pose)
    turn = random.random() * pi - pi/2
    move = random.random() * 2
    self.simbot.move(turn,move)
    sensorDict ={}
    sensorDict['id'] = 0
    sensorDict['msg'] = 'localizer.Fake_IPC'
    sensorDict['heading'] = self.simbot.theta
    sensorDict['accel'] = { 'x': 0, 'y': 0, 'z' : 980 }
    sensorDict['ultrasonic'] = self.simbot.sense(self.map)

    # %todo: x, y, theta -> dx, dy, dtheta
    msg = {'dTheta': turn, 'dXY': move, 'sensorData': sensorDict, 'timestamp': None}
    time.sleep(self.delay)
    return msg

#################################

class DumbLocalizer(object):
  def __init__(self, start_pose):
    self.r = robot.SimRobot(start_pose)
  def move(self, turn, move):
    self.r.move(turn, move)
  def update(self, sensors):
    pass
  def guess(self):
    return self.r.pose

#################################

if __name__ == '__main__':

  logging.config.fileConfig('logging.conf')  # local version
  logger = logging.getLogger(__name__)

  #m = map.Map('maps/test3.map')
  map_obj = mapping.pickler.unpickle_map('../mapping/map.pkl')
  waypoints = mapping.pickler.unpickle_waypoints('../mapping/waypoints.pkl')

  bot_loc = {'x': 6.0, 'y': 2.6, 'theta':pi/2}
  zones = { 'St01': True, 'St02': True, 'St03': False}
  map_props = {}
  bot_state = {'zone_change': 1}

  run(bot_loc, zones, map_props, map_obj, waypoints, None, bot_state, logger)

