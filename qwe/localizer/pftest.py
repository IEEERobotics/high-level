#!/usr/bin/python

from numpy import pi, array
from numpy.random import random
from numpy.linalg import norm
import time

import localizer
import robot, particles, map
from sensors import Ultrasonic
from pose import Pose
import std_sensors
import std_noise

import argparse
import signal
import sys

def signal_handler(signal, frame):
  print
  print score
  print error
  sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

score = []
error = []

parser = argparse.ArgumentParser(description='Particle Filter Tester')
parser.add_argument('-n', '--num', help='Number of partiles', type=int, default='500' )
parser.add_argument('-m', '--map', help='Map file', default='maps/test3.map' )
parser.add_argument('-r', '--res', help='Map res (inchs/block)', type=float, default='3.0' )
args = parser.parse_args()

m = map.Map(args.map, args.res)

start_x = m.x_inches / 2
start_y = m.y_inches / 2

start_pose = Pose(start_x, start_y, 0.0)
noise_params = std_noise.noise_params

# keep track of where we would have ended up with ideal motion
#  - no map required since we'll never call sense
#ideal = robot.SimRobot(pose = start_pose, sensors = std_sensors.sensors)
ideal = robot.SimRobot(pose = start_pose)

# simulated robot
#  - keeps track of where the robot would actually be
#  - movement updates are noisy, so our x,y,theta don't match ideal
#  - noisy sensors, responses based on the map we're simulating
simbot = robot.SimRobot(pose = start_pose, sensors = std_sensors.sensors, noise_params = noise_params)

# particle filter based localization logic
# TODO: need to be able to pass in a "tightness" (variance of the resampling gaussian)
#p = particles.Particles(r, m, num)

# create a localizer using the robot as a model
# TODO: decide if we shold be using an ideal or noisy movement/sensors
ploc = particles.ParticleLocalizer(std_sensors.sensors, noise_params, m, args.num)
dloc = localizer.DumbLocalizer(start_pose)

print "Start: ", simbot
print

while True:
#for n in range(20):
  # turn and move commands would normally be received from navigator over IPC queue
  turn = random() * pi - pi/2
  move = random() * 1
  print "Turn: %+0.2f, Move: %0.2f" % (turn, move)

  # this is what would happen in a perfect world
  #ideal.move(turn, move)
  # simulate the imperfect world
  simbot.move(turn, move)
  measured = simbot.sense(m)

  # let the localizer know what we tried to do
  dloc.move(turn, move)
  ploc.move(turn, move)

  # calculate particle sense, compare with measurements, update guess
  # - this is a noop for DumbLocalizer
  dloc.update(measured)
  ploc.update(measured)
  print "Robot: ", simbot
  #print "Ideal: (%0.2f, %0.2f) @ %+0.2f" % (ideal.x, ideal.y, ideal.theta)

  dguess = dloc.guess()
  derr_xy = norm([simbot.x - dguess.x, simbot.y - dguess.y])
  derr_theta = abs(simbot.theta - dguess.theta)
  if derr_theta > pi:
    derr_theta = 2*pi - derr_theta
  print "Dumb Guess: ", dguess, 
  print " Error: %0.2f @ %0.2f" % (derr_xy, derr_theta)

  pguess = ploc.guess_mean()
  perr_xy = norm([simbot.x - pguess.x, simbot.y - pguess.y])
  perr_theta = abs(simbot.theta - pguess.theta)
  if perr_theta > pi:
    perr_theta = 2*pi - perr_theta
  print "Part Guess (mean): ", pguess,
  print " Error: %0.2f @ %0.2f" % (perr_xy, perr_theta)

  bguess = ploc.guess_best()
  perr_xy = norm([simbot.x - bguess.x, simbot.y - bguess.y])
  perr_theta = abs(simbot.theta - bguess.theta)
  if perr_theta > pi:
    perr_theta = 2*pi - perr_theta
  print "Part Guess (best): ", bguess,
  print " Error: %0.2f @ %0.2f" % (perr_xy, perr_theta)

  pwguess = ploc.guess_wmean()
  perr_xy = norm([simbot.x - pwguess.x, simbot.y - pwguess.y])
  perr_theta = abs(simbot.theta - pwguess.theta)
  if perr_theta > pi:
    perr_theta = 2*pi - perr_theta
  print "Part Guess (weighted): ", pwguess,
  print " Error: %0.2f @ %0.2f" % (perr_xy, perr_theta)

  score.append( ploc.score() )
  error.append( perr_xy )

  print

  #time.sleep(0.5) 
