# Enthought library imports
from enable.api import Component, ComponentEditor
from traits.api import \
        HasTraits, Instance, Property, DelegatesTo, \
        Int, Float, Array, Range, cached_property
from traitsui.api import Item, View, Group

# Chaco imports
from chaco.api import ArrayDataSource, MultiArrayDataSource, DataRange1D, \
        LinearMapper, ScatterPlot, QuiverPlot, Plot, ArrayPlotData, LinePlot

from robot import *

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

    plot.aspect_ratio = float(self.xsize) / float(self.ysize)
    return plot
     

if __name__ == "__main__":
  r = Robot( x = 5.0, y = 5.0, theta = 0.0 )
  plot = RobotPlot(robot = r)
  plot.configure_traits()

  #Simulator(robot = r).configure_traits()
