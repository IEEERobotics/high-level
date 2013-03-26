import map
import raycast
from numpy import random
import pose

from numpy import pi
from numpy.linalg import norm

class Sensor(object):
  name = ''
  def __init__(self, name):
    self.name = name

class Ultrasonic(Sensor):
  def __init__(self, name, rel_pose, noise = 0.0):  # better to use *args, **kwargs??
    Sensor.__init__(self, name)
    self.rel_pose = rel_pose # relative to robot center (inches)
    self.noise = noise # 1st std deviation, so 2*noise is 95%
    self.max = 196.0  # inches
    # TODO: figure out how we convert this precision value to gaussians
    self.resolution = 0.1  # inches, from datasheet (0.3cm)

  def sense(self, pose, map, noisy = False):
    """
    Calculates ultrasonic sensor response

    Parameters
    ----------
    pose -- robot absolute coordinates and angle (inches)
    """
    sense_pose = pose + self.rel_pose
    # TODO: ultrasonic sense should be a +/-15 degree cone - calc 3 times and take closest?
    wx,wy = raycast.wall(sense_pose.x /map.scale, sense_pose.y/map.scale, sense_pose.theta, map)
    if wx == -1:  # no wall seen
     val = self.max
    else:
      wx *= map.scale
      wy *= map.scale
      val = norm( [sense_pose.x-wx, sense_pose.y-wy] )
      if noisy:
        val += random.normal(0, self.noise)
    # TODO: figure out if particles should use dirty sensors (guess: no?)
    return val

class Compass(Sensor):
  def __init__(self, index, name):
    Sensor.__init__(self, index, name)

class Accelerometer(Sensor):
  def __init__(self, index, name):
    Sensor.__init__(self, index, name)
  
