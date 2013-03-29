import map
import raycast
from numpy import random
from pose import *

from numpy import pi
from numpy.linalg import norm

class Sensor(object):
  name = ''
  def __init__(self, name):
    self.name = name

class Ultrasonic(Sensor):
  def __init__(self, name, rel_pose, noise = 0.0, cone = False):  # better to use *args, **kwargs??
    Sensor.__init__(self, name)
    self.rel_pose = rel_pose # relative to robot center (inches)
    self.noise = noise # 1st std deviation, so 2*noise is 95%
    self.max = 196.0  # inches
    # TODO: figure out how we convert this precision value to gaussians
    self.resolution = 0.1  # inches, from datasheet (0.3cm)
    self.cone = cone

  def sense(self, pose, map, noisy = False):
    if self.cone:  # 15 degree cone
      left = self.sense1(pose + Pose(0,0,-pi/12), map, noisy)
      center = self.sense1(pose, map,noisy)
      right = self.sense1(pose + Pose(0,0,pi/12), map, noisy)
      return min([left,center,right])
    else:
      return self.sense1(pose, map, noisy)

  def sense1(self, pose, map, noisy):
    """
    Calculates ultrasonic sensor response

    Parameters
    ----------
    pose -- robot absolute coordinates and angle (inches)
    """
    sense_pose = pose + self.rel_pose
    #print "Sense1 pose: ", sense_pose
    # TODO: ultrasonic sense should be a +/-15 degree cone - calc 3 times and take closest?
    #wx,wy = raycast.wall(sense_pose.x, sense_pose.y, sense_pose.theta, map, self.max)
    wx,wy = raycast.find_wall(sense_pose.x, sense_pose.y, sense_pose.theta, self.max, map)
    #print "Wall sense: ", wx, wy
    if wx <0:  # no wall seen
     val = self.max
    else:
      val = norm( [sense_pose.x-wx, sense_pose.y-wy] )
      if noisy:
        val += random.normal(0, self.noise)
    # TODO: figure out if particles should use dirty sensors (guess: no?)
    #print "Sense1 val: ", val
    return val

class Compass(Sensor):
  def __init__(self, index, name):
    Sensor.__init__(self, index, name)

class Accelerometer(Sensor):
  def __init__(self, index, name):
    Sensor.__init__(self, index, name)
  
