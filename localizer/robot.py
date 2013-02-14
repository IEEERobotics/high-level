# Major library imports
from numpy import array, sort, pi, cos, sin
from numpy.linalg import norm
# from numpy.random import random
from raycast import wall
from random import gauss

# Enthought library imports
from enable.api import Component, ComponentEditor
from traits.api import \
        HasTraits, Instance, Property, DelegatesTo, \
        Int, Float, Array, Range, cached_property
from traitsui.api import Item, View, Group

# Chaco imports
from chaco.api import ArrayDataSource, MultiArrayDataSource, DataRange1D, \
        LinearMapper, ScatterPlot, QuiverPlot, Plot, ArrayPlotData, LinePlot

from sensors import *

class MapPlot(HasTraits):
    plot = Instance(Plot)

class Robot(HasTraits):

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

  def sense_all(self, mapdata):
    #print "Robot sense:"
    sensed = []
    for s in self.sensors:
      val = self.sense(s.angle, mapdata)
      sensed.append(val)
    return sensed

  # a simulator stub of the robot's sensors
  #   currently a very simple model -- straightline distance to closest wall
  def sense(self, rel_theta, mapdata):
    sense_theta = (self.theta + rel_theta) % (2*pi)
    # TODO: this needs to sense in a 30(?) degree arc, not just straight ahead
    wx,wy = wall(self.x,self.y,sense_theta,mapdata)
    # mimic sensor by calculating euclidian distance + noise
    return norm([self.x - wx, self.y - wy]) + gauss(0,self.noise_sense)

  # simulator stub for moving the robot 
  #   all moves are : turn, then go forward
  def move(self, dtheta, forward):
    print "Move [dtheta, forward] : %+0.2f, %0.2f " % (dtheta, forward)
    self.theta = (self.theta + dtheta) % (2*pi)   # range must stay [0,2*pi]
    self.theta = gauss(self.theta, self.noise_turn * dtheta)
    dx = forward * cos(self.theta)
    dy = forward * sin(self.theta)
    self.x += dx
    self.y += dy
    self.x = gauss(self.x, self.noise_move * dx)
    self.y = gauss(self.y, self.noise_move * dy)

class RobotPlotter(HasTraits):

  robot = Instance(Robot)
  plot = Instance(Component)
  vsize = Int(10)
  xsize = Int
  ysize = Int

  # these delegations allow the _*_changed notifications to work
  #  since robot is nolonger traitsified... remove?
  x = DelegatesTo('robot')
  y = DelegatesTo('robot')
  theta = DelegatesTo('robot')
  color = DelegatesTo('robot')

  vector = Property(Array, depends_on=["theta"])

  # this defines the default view when configure_traits is called
  traits_view = View(Item('robot'),
                     Item('plot', editor=ComponentEditor(), show_label=False),
                     resizable=True)

  def do_redraw(self):
    self.plot.index.set_data([self.robot.x])
    self.plot.value.set_data([self.robot.y])
    self.plot.vectors.set_data(self.vector)
    self.plot.request_redraw()

  #def _x_changed(self):
  #  # these should probably reference a named datasource handle (x_ds, y_ds)
  #  # instead of the ones inside plot (index, value)
  #  self.plot.index.set_data([self.x])
  #  self.plot.request_redraw()

  #def _y_changed(self):
  #  self.plot.value.set_data([self.y])
  #  self.plot.request_redraw()

  #def _theta_changed(self):
  #  self.plot.vectors.set_data(self.vector)
  #  self.plot.request_redraw()

  # getter for vector property
  def _get_vector(self):
    return array([[cos(self.theta), sin(self.theta)]])*self.vsize

  # dynamic instantiation of plot
  def _plot_default(self):

    #xsize = self.robot.xmax
    #ysize = self.robot.ymax

    # Array data sources, each single element arrays
    x_ds = ArrayDataSource([self.x])
    y_ds = ArrayDataSource([self.y])

    vector_ds = MultiArrayDataSource()
    vector_ds.set_data(self.vector)

    # Set up the ranges for the plot explicitly (no autosizing)
    x_r = DataRange1D(x_ds)
    x_r.set_bounds(0,self.xsize)
    y_r = DataRange1D(y_ds)
    y_r.set_bounds(0,self.ysize)

    plot = QuiverPlot(index = x_ds, value = y_ds,
                    vectors = vector_ds,
                    index_mapper = LinearMapper(range=x_r),
                    value_mapper = LinearMapper(range=y_r),
                    bgcolor = "white", line_color = self.color, line_width = 2.0)

    plot.aspect_ratio = self.xsize / self.ysize
    return plot
     

if __name__ == "__main__":
  r = Robot( x = 5.0, y = 5.0, theta = 0.0 )
  plot = RobotPlot(robot = r)
  plot.configure_traits()

  #Simulator(robot = r).configure_traits()
