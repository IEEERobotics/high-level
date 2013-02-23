import map
import raycast

from numpy import pi
from numpy.linalg import norm

class Sensor(object):
  index = 0
  name = ''
  def __init__(self, index, name):
    self.index = index
    self.name = name

class Ultrasonic(Sensor):
  def __init__(self, index, name, angle):  # better to use *args, **kwargs??
    Sensor.__init__(self, index, name)
    self.angle = angle
    # TODO: add sensor position offsets (x,y) from center of robot?? 
    self.max = 196.0  # inches

  # TODO: ultrasonic sense should be a 30 degree cone - calc 3 times and take closest?
  def sense(self, rx, ry, rtheta, map):
    """
    Calculates sensor response

    Parameters
    ----------
    rx, ry, rtheta -- robot absolute coordinates and angle
    """
    sense_theta = (rtheta + self.angle) % (2*pi)
    wx,wy = raycast.wall(rx, ry, sense_theta, map)
    if wx == -1:  # no wall seen
     val = self.max / map.scale  # inches / (inches/square)
    else:
      val = norm( [rx-wx, ry-wy] )
    # right now, we're only adding noise explictly in Robot.sense(), 
    # so return the "perfect" value here
    # TODO: figure out if particles should use dirty sensors
    return val

class Compass(Sensor):
  def __init__(self, index, name):
    Sensor.__init__(self, index, name)

class Accelerometer(Sensor):
  def __init__(self, index, name):
    Sensor.__init__(self, index, name)
  
