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
    sensors.append(Ultrasonic(FORWARD,'F',0.0))
    sensors.append(Ultrasonic(LEFT,'L',pi/2))
    sensors.append(Ultrasonic(RIGHT,'R',-pi/2))
    self.sensors = sensors

  def __str__(self):
    return " (%5.2f , %5.2f)  @ %+0.2f\n" % (self.x, self.y, self.theta)

  # a simulator stub of the robot's sensors
  #   currently a very simple model -- straightline distance to closest wall
  def sense_all(self, map):
    #print "Robot sense:"
    sensed = []
    for s in self.sensors:
      #val = self.sense(s.angle, map)
      val = s.sense(self.x, self.y, self.theta, map)
      val += gauss(0, self.noise_sense)  # simulate noise
      sensed.append(val)
    return sensed

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

