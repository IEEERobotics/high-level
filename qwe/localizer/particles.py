#!/usr/bin/python

# Major library imports
from numpy import array, sort, pi, cos, sin, zeros, arctan2
from numpy import random  # for random.random, random.normal (gaussian)

# for sense 
from raycast import wall
from numpy.linalg import norm
from probability import gaussian, ngaussian

from robot import *
from pose import *

class ParticleLocalizer(object):
  # things we need from robot for init:
  #  - ? noise params?
  #
  # public: move(), update(), score()
  #
  def __init__(self, sensor_list, noise_params, map, pcount, start_pose = None, logger = None):

    self.p = Particles(sensor_list, noise_params, map, pcount, start_pose, logger = logger)
    self.pcount = pcount
    self.weight = zeros(pcount)    # probability measurement, "weight"
    self.raw_error = zeros(pcount)
    self.logger = logger
    logger.debug("ParticleLocalizer (N=%d) initialized, Start pose: %s" % (pcount, start_pose))

    self.score_hist = []
    
  def move(self, turn, move):
    # this seems silly
    self.p.move(turn, move)

  # Sense, weigh, and resample
  def update(self, measured):

    self.logger.debug("ParticleLocalizer: update using: %s" % measured)
    old = self.score()
    self.p.particle_sense()
    self.calc_weights(measured)
    new = self.score()
    #if new > old:
    #  print "Improved!!"
    #  self.resample()
    #else:
    #  self.resample(10.0)
    #  print "Worse"

    self.resample(0.0)
    self.logger.debug("ParticleLocalizer: update copmlete")

  # Sense and Resample
  def score(self):
    total = self.weight.sum()
    mean = self.weight.mean()
    best = self.weight.max()
    std = self.weight.std()
    raw = self.raw_error.mean()
    self.score_hist.append(mean)
    #print "Scores: mean: %0.4f, best: %0.4f, std %0.4f, raw: %0.2f" % (mean, best, std, raw)
    return mean

  def calc_weights(self, measured):
    #print "Particles: updating weights:"
    # create an array of particle weights to use as resampling probability
    prob = self.weight
    raw = self.raw_error
    for i in range(self.pcount):
      # what if we init to 1.0 once, then refine this probability continuously?
      prob[i] = 1.0
      raw[i] = 0
      #print self.p.x[i], self.p.y[i]
      # TODO test particle on wall
      if not ((0 <= self.p.x[i] <= self.p.map.x_inches) and (0 <= self.p.y[i] <= self.p.map.y_inches)):
        self.logger.warn("Bad ploc: (%0.2f, %0.2f)! Setting weight to 0.0" % (self.p.x[i], self.p.y[i]))
        prob[i] = 0.0
      for name,sensor in self.p.sensors.items():
        # only weight valid sensor data
        if measured[name] >= 0:
          # compare measured input of sensor versus the particle's value, adjusting prob accordingly
          #         perhaps this should actually just lookup the measurement difference in
          #         a precomputed PDF for the sensor (gaussian around zero diff and a bump at max)
          prob[i] *= ngaussian(self.p.sensed[name][i], sensor.gauss_var, measured[name])
          raw[i] += abs(self.p.sensed[name][i] - measured[name])
          #print "sensor: %s, sense: %0.2f, meas %0.2f, prob: %0.4f" % (name, self.p.sensed[name][i], measured[name], prob[i])
        else:
          pass
          #print "sensor: %s, bad reading, skipping" % name
      #print "  %d : raw_err: %0.2f,  prob: %0.2f" % (i, raw[i], prob[i])
      #print

  def random_particles(self, count):
    x = random.random(count) * self.p.map.x_inches
    y = random.random(count) * self.p.map.y_inches
    theta = random.random(count)*2*pi
    return zip( zeros(len(x)), x, y, theta, zeros(len(x)) )

  def resample(self, rand_percent = 0.0):
    x = self.p.x
    y = self.p.y
    theta = self.p.theta
    weight = self.weight
    if weight.sum() == 0.0:
      self.logger.warn("Zero particle weights, skipping resample!")
      print "Zero particle weights, skipping resample!"
      return
    # resample (x, y, theta) using wheel resampler
    rand_count = int(self.pcount * (rand_percent/100.0))  # use some% entirely random
    #print "New random: %d" % rand_count
    new = self.random_particles(rand_count)
    step = max(weight) * 2.0
    cur = int(random.random() * self.pcount)
    beta = 0.0
    for i in range(self.pcount - rand_count):
      beta += random.random() * step  # 0 - step size
      while beta > weight[cur]:
        beta -= weight[cur]
        cur = (cur+1) % self.pcount
        #print "b: %0.2f, cur: %d, prob = %0.2f" % (beta, cur, weight[cur])
      new.append((cur, x[cur], y[cur], theta[cur], weight[cur]))
    #print "Resampled:"
    #for i in range(self.pcount):
    #  print " %d : %0.2f, %0.2f @ %+0.2f = %0.2e " % new[i]
    self.p.x = array([e[1] for e in new])
    self.p.y = array([e[2] for e in new])
    self.p.theta = array([e[3] for e in new])

  # TODO: try using a guess based on weighted particles?
  def guess(self):
    return self.guess_wmean()
    #return self.guess_best()

  def guess_mean(self):
    x = self.p.x.mean()
    y = self.p.y.mean()
    # average the vector components of theta individually to avoid jump between 0 and 2pi
    vx,vy = self.p.v.mean(axis=0)
    theta = arctan2(vy,vx) % (2*pi)
    return Pose(x,y,theta)

  def guess_wmean(self):
    weight = self.weight
    normalizer = weight.sum()
    if normalizer > 0.0:
      self.logger.debug("particle weight normalizer: %0.4f", normalizer)
      x = (self.p.x * weight).sum() / normalizer
      y = (self.p.y * weight).sum() / normalizer
      # average the vector components of theta individually to avoid jump between 0 and 2pi
      vx = (self.p.v[:,0] * weight).sum() / normalizer
      vy = (self.p.v[:,1] * weight).sum() / normalizer
      theta = arctan2(vy,vx) % (2*pi)
    else:
      self.logger.warn('Zero particle weight normalizer!!')
      return self.guess_mean()
    return Pose(x,y,theta)

  def guess_best(self):
    max_index = self.weight.argmax()
    x = self.p.x[max_index]
    y = self.p.y[max_index]
    theta = self.p.theta[max_index]
    return Pose(x,y,theta)
    

######################################################

class Particles(object):
  """ Essentially a large array of simbots (pose, sensor list, and noise params) """

  def __init__(self, sensors, noise, map, pcount = 100, start_pose = None, logger = None):
    # initialize particle filter
    #  - number of particles
    #  - map
    #  - robot params: sensors, movement error/noise
    self.pcount = pcount
    self.map = map
    self.sensors = sensors
    self.sensed = {}
    for s in sensors:
      self.sensed[s] = zeros(self.pcount)  # modeled sensor data
    self.noise = noise
    self.logger = logger

    # Create starting points for the vectors.

    if not start_pose:
      self.x = sort(random.random(self.pcount)) * map.x_inches  # only sorted for gui axis auto sizing?
      self.y = random.random(self.pcount) * map.y_inches
      self.theta = random.random(self.pcount)*2*pi
    else:
      xy_var = noise['move']
      theta_var = noise['turn']
      self.x = random.randn(self.pcount) * xy_var*2 + start_pose.x
      self.y = random.randn(self.pcount) * xy_var*2 + start_pose.y
      self.theta = random.randn(self.pcount) * theta_var*2 + start_pose.theta

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
    self.y = y.clip(0,self.map.y_inches)
    self.x = x.clip(0,self.map.x_inches)

    self.theta = theta

  # called by update
  def particle_sense(self):
    self.logger.debug("ParticleLocalizer: particle_sense begin")
    x = self.x
    y = self.y
    for name,sensor in self.sensors.items():
      # get the full set of particle senses for this sensor
      for i in range(self.pcount):
        self.sensed[name][i] = sensor.sense(Pose(self.x[i], self.y[i], self.theta[i]), self.map)
    #print "Particle sense:"
    #for i in range(self.pcount):
    #  print "  %0.2f, %0.2f @ %0.2f = " % (x[i], y[i], self.theta[i]),
    #  print ", ".join( [ "%s: %0.2f" % (s.name, self.sensed[s.index,i]) for s in self.robot.sensors ])
    self.logger.debug("ParticleLocalizer: particle_sense complete")

