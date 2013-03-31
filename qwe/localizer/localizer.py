#!/usr/bin/python

from numpy import random, pi, zeros

import robot, particles, map, pose
import time  # sleep

import std_sensors, std_noise

import sys
sys.path.append('..')
import mapping.map_class
sys.modules['map_class'] = mapping.map_class  # deal with the fact we pickled a module in another dir
import mapping.pickler

# blocks status + map = walls 
#def run( start_x, start_y, start_theta, ipc_channel = None, shared_data = {}, map_data = None ):
def run( bot_loc, blocks, map_properties, course_map, ipc_channel, bot_state ):
  
  start_pose = pose.Pose(bot_loc["x"],bot_loc["y"],bot_loc["theta"])
  #start_pose = pose.Pose(start_x,start_y,start_theta)
  ideal = robot.SimRobot(start_pose, std_sensors.default)

  themap = map.Map.from_map_class(course_map)

  if not ipc_channel:
    print "Using stub IPC"
    ipc_channel = Fake_IPC(start_pose, themap, delay = 1.0)

  print "Start: ", start_pose
  print

  localizer = DumbLocalizer(start_pose)
  #localizer = particles.ParticleLocalizer(std_sensors.default, std_noise.noise_params, map_data, pcount=1000)

  while True:
    msg = ipc_channel.get()
    turn, move = msg['dTheta'], msg['dXY']
    sensors = msg['sensorData']
    print "Message: Turn: %+0.2f, Move: %0.2f" % (turn, move)
    print "Sensors: ", sensors
    ideal.move(turn, move)
    localizer.move(turn, move)
    print "Ideal: ", ideal.pose
    localizer.update(sensors)
    guess = localizer.guess()
    print "Guess: ", guess
    print
    bot_loc['x'] = guess.x
    bot_loc['y'] = guess.y
    bot_loc['theta'] = guess.theta
    bot_loc['dirty'] = False

#################################
class Fake_IPC(object):
  def __init__(self, start_pose, map_data, delay = 0.0):
    self.delay = delay
    self.map = map_data
    self.simbot = robot.SimRobot(pose = start_pose, sensors = std_sensors.default, 
                            noise_params = std_noise.noise_params)

  def get(self):
    print "SimBot: ", self.simbot.pose
    turn = random.random() * pi - pi/2
    move = random.random() * 2
    self.simbot.move(turn,move)
    measured = self.simbot.sense(self.map)
    # %todo: x, y, theta -> dx, dy, dtheta
    msg = {'dTheta': turn, 'dXY': move, 'sensorData': measured, 'timestamp': None}
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

