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

# blocks status + map = walls 
#def run( start_x, start_y, start_theta, ipc_channel = None, shared_data = {}, map_data = None ):
def run( bot_loc, blocks, map_properties, course_map, ipc_channel, bot_state, logger=None ):

  if logger is None: 
    if not os.getcwd().endswith('qwe'):
      oldcwd = os.getcwd()
      os.chdir('..')
      logging.config.fileConfig('logging.conf')
      logger = logging.getLogger(__name__)
      os.chdir(oldcwd)
    else:
      logging.config.fileConfig('logging.conf')
      logger = logging.getLogger(__name__)

  start_pose = pose.Pose(bot_loc["x"],bot_loc["y"],bot_loc["theta"])
  ideal = robot.SimRobot(start_pose, std_sensors.offset_str)

  themap = map.Map.from_map_class(course_map)
  logger.debug("Map dimensions: %s" % themap)

  if not ipc_channel:
    logging.debug("Using Fake_IPC queue")
    ipc_channel = Fake_IPC(start_pose, themap, delay = 1.0, logger = logger)

  #localizer = DumbLocalizer(start_pose)
  localizer = particles.ParticleLocalizer(std_sensors.offset_str, std_noise.noise_params, themap, 500, start_pose)

  while True:
    msg = ipc_channel.get()
    turn, move = msg['dTheta'], msg['dXY']
    sensors = msg['sensorData']
    logger.debug("From qNav: Turn: %+0.2f, Move: %0.2f" % (turn, move))
    logger.debug( "Sensors dict: %s" % sensors)

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
  def __init__(self, start_pose, map_data, delay = 0.0, logger = None):
    self.delay = delay
    self.logger = logger
    self.map = map_data
    self.simbot = robot.SimRobot(pose = start_pose, sensors = std_sensors.offset_str, 
                            noise_params = std_noise.noise_params)
    sensed = self.simbot.sense(self.map)
    logger.debug( "Initial pose: %s" % self.simbot)
    logger.debug( "Initial sense: %s" % sensed)

  def get(self):
    self.logger.debug("SimBot pose: %s" % self.simbot.pose)
    turn = random.random() * pi - pi/2
    move = random.random() * 2
    self.simbot.move(turn,move)
    sensorDict = self.simbot.sense(self.map)

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

  #m = map.Map('maps/test3.map')
  map_obj = mapping.pickler.unpickle_map('../mapping/map.pkl')

  bot_loc = {'x': 6.0, 'y': 2.6, 'theta':pi/2}
  blocks = {}
  map_props = {}
  bot_state = {}

  run(bot_loc, blocks, map_props, map_obj, None, bot_state)
  #def run( bot_loc, blocks, map_properties, course_map, ipc_channel, bot_state ):

