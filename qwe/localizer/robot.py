# Major library imports
from numpy import array, sort, pi, cos, sin
from numpy.linalg import norm

from raycast import wall
from random import gauss

from sensors import *

class Robot(object):

  def __init__(self, x, y, theta, color = 'red', noise_move = 0.1, noise_turn = 0.1, noise_sense = 0.25):

    self.x = x
    self.y = y
    self.theta = theta
    self.color = color

    # noise params, contributes to gaussian noise sigma (std dev)
    self.noise_move = noise_move
    self.noise_turn = noise_turn
    self.noise_sense = noise_sense

    self.num_sensors = 3
    sensors = []
    FORWARD, LEFT, RIGHT = range(self.num_sensors)  
    sensors.append(Sensor(FORWARD,'F',0.0))
    sensors.append(Sensor(LEFT,'L',pi/2))
    sensors.append(Sensor(RIGHT,'R',-pi/2))
    self.sensors = sensors

  def __str__(self):
    return " (%5.2f , %5.2f)  @ %+0.2f\n" % (self.x, self.y, self.theta)

  def sense_all(self, map):
    #print "Robot sense:"
    sensed = []
    for s in self.sensors:
      val = self.sense(s.angle, map)
      sensed.append(val)
    return sensed

  # a simulator stub of the robot's sensors
  #   currently a very simple model -- straightline distance to closest wall
  def sense(self, rel_theta, map):
    sense_theta = (self.theta + rel_theta) % (2*pi)
    # TODO: this needs to sense in a 30(?) degree arc, not just straight ahead
    wx,wy = wall(self.x,self.y,sense_theta,map)
    if wx == -1:  # no wall seen
      data = norm( [map.xdim, map.ydim] )  # TODO should be sensor max reading
    else:
      # mimic sensor by calculating euclidian distance + noise
      data = norm( [self.x-wx, self.y-wy] )
      # add simulated noise
      data += gauss(0, self.noise_sense)
    return data

  # simulator stub for moving the robot 
  #   all moves are : turn, then go forward
  def move(self, dtheta, forward):
    #print "Move [dtheta, forward] : %+0.2f, %0.2f " % (dtheta, forward)
    self.theta = gauss(self.theta + dtheta , self.noise_turn * dtheta) % (2*pi)
    dx = forward * cos(self.theta)
    dy = forward * sin(self.theta)
    self.x += dx
    self.y += dy
    self.x = gauss(self.x, self.noise_move * dx)
    self.y = gauss(self.y, self.noise_move * dy)

