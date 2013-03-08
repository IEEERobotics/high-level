#!/usr/bin/python

# Major library imports
from numpy import array, sort, pi, cos, sin, zeros, arctan2
from numpy import random  # for random.random, random.normal (gaussian)

# for sense 
from raycast import wall
from numpy.linalg import norm
from probability import gaussian 

from robot import *
from pose import *

class ParticleLocalizer(object):
  # things we need from robot for init:
  #  - sensor list
  #  - ? noise params?
  def __init__(self, sensor_list, noise_params, map, pcount):
    self.p = Particles(sensor_list, noise_params, map, pcount)
    self.pcount = pcount
    self.prob = zeros(pcount)    # probability measurement, "weight"
    
  def move(self, turn, move):
    # this seems silly
    self.p.move(turn, move)
    
  # Sense and Resample
  def update(self, measured):
    self.p.particle_sense()
    self.resample(measured)

  def resample(self, measured):
    x = self.p.x
    y = self.p.y
    theta = self.p.theta
    #print "Particles: updating weights:"
    # create an array of particle weights to use as resampling probability
    for i in range(self.pcount):
      self.prob[i] = 1.0
      for index,s in enumerate(self.p.sensors):
        # compare measured input of sensor versus the particle's value, adjusting prob accordingly
        #   TODO: refine 1.0 noise parameter to something meaningful
        self.prob[i] *= gaussian(self.p.sensed[index][i], 1.5, measured[index])
      #print "  %d : %0.2f, %0.2f @ %0.2f = %0.2e" % (i, x[i], y[i], theta[i], self.prob[i]) 

    # resample (x, y, theta) using wheel resampler
    new = []
    step = max(self.prob) * 2.0
    cur = int(random.random() * self.pcount)
    beta = 0.0
    for i in range(self.pcount):
      beta += random.random() * step  # 0 - step size
      while beta > self.prob[cur]:
        beta -= self.prob[cur]
        cur = (cur+1) % self.pcount
        #print "b: %0.2f, cur: %d, prob = %0.2f" % (beta, cur, self.prob[cur])
      new.append((cur, x[cur], y[cur], theta[cur], self.prob[cur]))
    #print "Resampled:"
    #for i in range(self.pcount):
    #  print " %d : %0.2f, %0.2f @ %+0.2f = %0.2e " % new[i]
    self.p.x = array([e[1] for e in new])
    self.p.y = array([e[2] for e in new])
    self.p.theta = array([e[3] for e in new])

  # TODO: try using a guess based on weighted particles?
  def guess(self):
    return self.guess_mean()

  def guess_mean(self):
    x = self.p.x.mean()
    y = self.p.y.mean()
    # average the vector components of theta individually to avoid jump between 0 and 2pi
    vx,vy = self.p.v.mean(axis=0)
    theta = arctan2(vy,vx) % (2*pi)
    return Pose(x,y,theta)

######################################################

class Particles(object):
  """ Essentially a large array of simbots (pose, sensor list, and noise params) """

  def __init__(self, sensors, noise, map, pcount = 100):
    # initialize particle filter
    #  - number of particles
    #  - map
    #  - robot params: sensors, movement error/noise
    self.pcount = pcount
    self.map = map
    self.sensed = zeros((len(sensors),self.pcount))  # modeled sensor data
    self.sensors = sensors
    self.noise = noise

    # Create starting points for the vectors.
    self.x = sort(random.random(self.pcount)) * map.xdim  # only sorted for gui axis auto sizing?
    self.y = random.random(self.pcount) * map.ydim
    self.theta = random.random(self.pcount)*2*pi


  def __str__(self):
    out = "Particles:\n"
    for i in range(self.pcount):
      out += " %3d : (%5.2f , %5.2f)  @ %+0.2f\n" % (i, self.x[i], self.y[i], self.theta[i])
    return out

  @property
  def v(self):
    return array( zip(cos(self.theta), sin(self.theta)) )

  # update particles based on movement model, predicting new pose
  #   ? how do we handle moving off map?  or into any wall?  just let resampling handle it?
  # TODO: decide if particles should include noisy movement
  def move(self, dtheta, forward):
    x = self.x
    y = self.y
    theta = self.theta
    for i in range(self.pcount):
      theta[i] = (theta[i] + dtheta) % (2*pi)
      theta[i] = gauss(theta[i], dtheta * self.noise['turn'])
      dx = forward * cos(theta[i])
      dy = forward * sin(theta[i])
      x[i] = gauss(x[i] + dx, dx * self.noise['move'])
      y[i] = gauss(y[i] + dy, dy * self.noise['move'])

    # quick and dirty, keep things in range
    self.y = y.clip(0,self.map.ydim)
    self.x = x.clip(0,self.map.xdim)

    self.theta = theta

  # called by update
  def particle_sense(self):
    x = self.x
    y = self.y
    for index,s in enumerate(self.sensors):
      # get the full set of particle senses for this sensor
      for i in range(self.pcount):
        self.sensed[index, i] = s.sense(Pose(self.x[i], self.y[i], self.theta[i]), self.map)
    #print "Particle sense:"
    #for i in range(self.pcount):
    #  print "  %0.2f, %0.2f @ %0.2f = " % (x[i], y[i], self.theta[i]),
    #  print ", ".join( [ "%s: %0.2f" % (s.name, self.sensed[s.index,i]) for s in self.robot.sensors ])

  # Currently assumes self.sensed and measured have both been updated
  # called by update to guarantee  sensedkkk
