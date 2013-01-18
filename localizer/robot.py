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

class MapPlot(HasTraits):
    plot = Instance(Plot)

class Robot(HasTraits):
    x = Range(0,11.0)  # need to init this range from a param to init
    y = Range(0,9.0)
    theta = Range(-pi,pi)

    # a simulator stub of the robot's sensors
    #   currently a very simple model -- straightline distance to closest wall
    def sense(self, mapdata):
      # TODO: this needs to sense in a 30(?) degree arc, not just straight ahead
      wx,wy = wall(self.x,self.y,self.theta,mapdata)
      # mimic sensor by calculating euclidian distance + noise
      return norm([self.x - wx, self.y - wy]) + gauss(0,0.25)

    # simulator stub for moving the robot 
    #   all moves are : turn, then go forward
    def move(self, dtheta, forward):
      print "Move (dtheta, forward): ", dtheta, forward
      self.theta = ( (self.theta + dtheta + pi) % (2*pi) ) - pi  # range must stay [-pi,pi]
      print " Expected theta: ", self.theta
      self.theta = gauss(self.theta, 0.1 * dtheta)
      print " Actual theta: ", self.theta
      dx = forward * cos(self.theta)
      dy = forward * sin(self.theta)
      self.x += dx
      self.y += dy
      print " Expected x,y: ", self.x, self.y
      self.x = gauss(self.x, 0.1 * dx)
      self.y = gauss(self.y, 0.1 * dy)
      print " Actual x,y: ", self.x, self.y


class RobotPlot(HasTraits):

    robot = Instance(Robot)
    #plot = Instance(QuiverPlot)
    plot = Instance(Component)
    vsize = Int(10)

    # these delegations allow the _*_changed notifications to work
    x = DelegatesTo('robot')
    y = DelegatesTo('robot')
    theta = DelegatesTo('robot')

    vector = Property(Array, depends_on=["theta"])

    # this defines the default view when configure_traits is called
    traits_view = View(Item('robot'),
                       Item('plot', editor=ComponentEditor(), show_label=False),
                       resizable=True)

    def _x_changed(self):
      # these should probably reference a named datasource handle (x_ds, y_ds)
      # instead of the ones inside plot (index, value)
      self.plot.index.set_data([self.x])
      self.plot.request_redraw()

    def _y_changed(self):
      self.plot.value.set_data([self.y])
      self.plot.request_redraw()

    def _theta_changed(self):
      self.plot.vectors.set_data(self.vector)
      self.plot.request_redraw()

    # getter for vector property
    def _get_vector(self):
      return array([[cos(self.theta), sin(self.theta)]])*self.vsize

    # dynamic instantiation of plot
    def _plot_default(self):

      xsize = 11.0  # should be init param
      ysize = 9.0

      # Array data sources, each single element arrays
      x_ds = ArrayDataSource([self.x])
      y_ds = ArrayDataSource([self.y])

      vector_ds = MultiArrayDataSource()
      vector_ds.set_data(self.vector)

      # Set up the ranges for the plot explicitly (no autosizing)
      x_r = DataRange1D(x_ds)
      x_r.set_bounds(0,xsize)
      y_r = DataRange1D(y_ds)
      y_r.set_bounds(0,ysize)

      plot = QuiverPlot(index = x_ds, value = y_ds,
                      vectors = vector_ds,
                      index_mapper = LinearMapper(range=x_r),
                      value_mapper = LinearMapper(range=y_r),
                      bgcolor = "white", line_color = "red", line_width = 2.0)

      plot.aspect_ratio = xsize / ysize
      return plot
     

if __name__ == "__main__":
  r = Robot( x = 5.0, y = 5.0, theta = 0.0 )
  plot = RobotPlot(robot = r)
  plot.configure_traits()

  #Simulator(robot = r).configure_traits()
