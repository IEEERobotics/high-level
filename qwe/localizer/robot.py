# Major library imports
from numpy import array, sort, pi, cos, sin
from numpy.linalg import norm

from raycast import wall
from random import gauss

from sensors import *
from pose import *

no_noise = {'move': 0.0, 'turn': 0.0}

# Abstract robot class
class Robot(object):
  def __init__(self, pose, sensors = []):
    self.pose = pose
    self.sensors = sensors 
    self.num_sensors = len(sensors)

  def __str__(self):
    return self.pose.__str__()

  @property
  def x(self):
    return self.pose.x
  @property
  def y(self):
    return self.pose.y
  @property
  def theta(self):
    return self.pose.theta

  def sense(self, map):
    pass
  def move(self, dtheta, forward):
    pass

################################################
class RealRobot(Robot):

  def __init__(self, pose, sensors):
    Robot.__init__(self, pose, sensors)
    self.sensed = []

  # Process sensor data from IPC channel, so sense_all() can be called
  def sensor_update(sensor_data):
    pass

  def sense(self, map):  # just ignore map?
    return self.sensed

####################################################
class SimRobot(Robot):

  def __init__(self, pose, sensors = [], noise_params = no_noise):
    Robot.__init__(self, pose, sensors)

    # noise params, contributes to gaussian noise sigma (std dev)
    self.noise_move = noise_params['move']
    self.noise_turn = noise_params['turn']

  # simulate sensor readings, based on map we we're given
  #   currently a very simple model -- straightline distance to closest wall
  def sense(self, map, noisy = True):
    #print "SimRobot: Robot sense:"
    sensed = {}
    for name,sensor in self.sensors.items():
      val = sensor.sense(self.pose, map, noisy = noisy)
      sensed[name] = val
    return sensed

  # simulate robot motion
  #   all moves are restricted to: turn first, then go forward
  # TODO(?): restrict moving off map / into walls
  def move(self, dtheta, forward):

    #print "SimRobot.move: [dtheta, forward] : %+0.2f, %0.2f " % (dtheta, forward)
    pose = self.pose

    # since turning is noisy, simulate it before we move forward
    # by turning via the compass sensor, error should be somewhat consistent across all turn sizes
    if abs(dtheta) > 0.0:
      pose += Pose(0,0, dtheta + self.noise_turn * random.randn())

    # TODO: add translation noise during turn (proportional to turn size?)

    dx = forward * cos(pose.theta)
    dy = forward * sin(pose.theta)
    # error from slippage, etc is proportional to distance travelled
    pose.x += dx + random.randn() * self.noise_move * abs(dx)
    pose.y += dy + random.randn() * self.noise_move * abs(dy)

    self.pose = pose
