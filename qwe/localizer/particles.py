#!/usr/bin/python

# Major library imports
from numpy import array, sort, pi, cos, sin, zeros, arctan2
from numpy.random import random

# for sense 
from raycast import wall
from numpy.linalg import norm
from probability import gaussian 
from random import gauss  

from robot import *

class Particles(object):

  @property
  def v(self):
    return array( zip(cos(self.theta), sin(self.theta)) )


  def __init__(self, robot, map, n = 100):
    # need to move the logic out of the GUI class and into its own particles class
    self.numpts = n
    self.map = map
    self.sensed = zeros((robot.num_sensors,self.numpts))  # modeled sensor data
    self.robot = robot

    # Create starting points for the vectors.
    self.x = sort(random(self.numpts)) * map.xdim  # sorted for axis tick calculation?
    self.y = random(self.numpts) * map.ydim
    self.theta = random(self.numpts)*2*pi

    self.prob = zeros(self.numpts)    # probability measurement, "weight"

  def __str__(self):
    out = "Particles:\n"
    for i in range(self.numpts):
      out += " %3d : (%5.2f , %5.2f)  @ %+0.2f\n" % (i, self.x[i], self.y[i], self.theta[i])
    return out

  # update particles based on movement model, predicting new pose
  #   ? how do we handle moving off map?  or into any wall?  just let resampling handle it?
  def move(self, dtheta, forward):
    x = self.x
    y = self.y
    theta = self.theta
    for i in range(self.numpts):
      theta[i] = (theta[i] + dtheta) % (2*pi)
      theta[i] = gauss(theta[i], dtheta * self.robot.noise_turn)
      dx = forward * cos(theta[i])
      dy = forward * sin(theta[i])
      x[i] = gauss(x[i] + dx, dx * self.robot.noise_move)
      y[i] = gauss(y[i] + dy, dy * self.robot.noise_move)

    # quick and dirty, keep things in range
    self.y = y.clip(0,self.map.ydim)
    self.x = x.clip(0,self.map.xdim)

    self.theta = theta

  def sense_all(self, map):
    x = self.x
    y = self.y
    for s in self.robot.sensors:
      # get the full set of particle senses for this sensor
      for i in range(self.numpts):
        self.sensed[s.index, i] = s.sense(self.x[i], self.y[i], self.theta[i], map)
    #print "Particle sense:"
    #for i in range(self.numpts):
    #  print "  %0.2f, %0.2f @ %0.2f = " % (x[i], y[i], self.theta[i]),
    #  print ", ".join( [ "%s: %0.2f" % (s.name, self.sensed[s.index,i]) for s in self.robot.sensors ])

  # Currently assumes self.sensed and measured have both been updated
  def resample(self, measured):
    x = self.x
    y = self.y
    theta = self.theta
    #print "Updating particle weights:"
    # create an array of particle weights to use as resampling probability
    for i in range(self.numpts):
      self.prob[i] = 1.0
      for s in self.robot.sensors:
        # compare measured input of sensor versus the particle's value, adjusting prob accordingly
        #   TODO: refine 1.0 noise parameter to something meaningful
        self.prob[i] *= gaussian(self.sensed[s.index][i], 1.5, measured[s.index])
      #print "  %d : %0.2f, %0.2f @ %0.2f = %0.2e" % (i, x[i], y[i], theta[i], self.prob[i]) 

    # resample (x, y, theta) using wheel resampler
    new = []
    step = max(self.prob) * 2.0
    cur = int(random() * self.numpts)
    beta = 0.0
    for i in range(self.numpts):
      beta += random() * step  # 0 - step size
      while beta > self.prob[cur]:
        beta -= self.prob[cur]
        cur = (cur+1) % self.numpts
        #print "b: %0.2f, cur: %d, prob = %0.2f" % (beta, cur, self.prob[cur])
      new.append((cur, x[cur], y[cur], theta[cur], self.prob[cur]))
    #print "Resampled:"
    #for i in range(self.numpts):
    #  print " %d : %0.2f, %0.2f @ %+0.2f = %0.2e " % new[i]
    self.x = array([e[1] for e in new])
    self.y = array([e[2] for e in new])
    self.theta = array([e[3] for e in new])

  # TODO: try using a guess based on weighted particles?
  def guess(self):
    return self.guess_mean()

  def guess_mean(self):
    x = self.x.mean()
    y = self.y.mean()
    # average the vector components of theta individually to avoid jump between 0 and 2pi
    vx,vy = self.v.mean(axis=0)
    theta = arctan2(vy,vx) % (2*pi)
    return (x,y,theta)

