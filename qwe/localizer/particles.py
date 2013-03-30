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
  def __init__(self, sensor_list, noise_params, map, pcount, start_pose = None):
    self.p = Particles(sensor_list, noise_params, map, pcount, start_pose)
    self.pcount = pcount
    self.weight = zeros(pcount)    # probability measurement, "weight"
    self.raw_error = zeros(pcount)

    self.score_hist = []
    
  def move(self, turn, move):
    # this seems silly
    self.p.move(turn, move)

  # Sense, weigh, and resample
  def update(self, measured):

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
    self.resample(10.0)

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
      for index,s in enumerate(self.p.sensors):
        # compare measured input of sensor versus the particle's value, adjusting prob accordingly
        #   TODO: refine 1.0 noise parameter to something meaningful
        #         perhaps this should actually just lookup the measurement difference in
        #         a precomputed PDF for the sensor (gaussian around zero diff and a bump at max)
        prob[i] *= ngaussian(self.p.sensed[index][i], 5.0, measured[index])
        raw[i] += abs(self.p.sensed[index][i] - measured[index])
      #print "  %d : %0.2f, %0.2f @ %0.2f = %0.2e" % (i, x[i], y[i], theta[i], prob[i]) 

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
    x = (self.p.x * weight).sum() / normalizer
    y = (self.p.y * weight).sum() / normalizer
    # average the vector components of theta individually to avoid jump between 0 and 2pi
    vx = (self.p.v[:,0] * weight).sum() / normalizer
    vy = (self.p.v[:,1] * weight).sum() / normalizer
    theta = arctan2(vy,vx) % (2*pi)
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

  def __init__(self, sensors, noise, map, pcount = 100, start_pose = None):
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

    if not start_pose:
      self.x = sort(random.random(self.pcount)) * map.x_inches  # only sorted for gui axis auto sizing?
      self.y = random.random(self.pcount) * map.y_inches
      self.theta = random.random(self.pcount)*2*pi
    else:
      xy_var = noise['move']
      theta_var = noise['turn']
      self.x = random.randn(self.pcount) * xy_var + start_pose.x
      self.y = random.randn(self.pcount) * xy_var + start_pose.y
      self.theta = random.randn(self.pcount) * theta_var + start_pose.theta

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
