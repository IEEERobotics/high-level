#!/usr/bin/python

from traits.api import HasTraits, Instance, Array, Property, Int
from traitsui.api import View, Item
from chaco.api import ScatterPlot, ArrayDataSource, DataRange1D, LinearMapper, \
                  add_default_axes, PlotGrid
from enable.api import ComponentEditor, Component

from map import *

class MapPlot(HasTraits):

  plot = Instance(Component)
  map = Instance(Map)
  data = Array  # 2d matrix map
  traits_view = View(Item('plot', editor=ComponentEditor(size = (480,400))),
                     resizable=False)

  xdim = Property(Int)
  ydim = Property(Int)

  def _get_xdim(self):
    return self.map.xdim

  def _get_ydim(self):
    return self.map.ydim

  def _plot_default(self):

    data_xy = self.map.xy()

    x_ds = ArrayDataSource(data_xy[:,0])
    y_ds = ArrayDataSource(data_xy[:,1])
    x_dr = DataRange1D(x_ds)
    y_dr = DataRange1D(y_ds)
    x_dr.set_bounds(0, self.map.xdim)  # auto ranging won't work if a side has no walls
    y_dr.set_bounds(0, self.map.ydim)

    markersize = max( min(475/self.map.ydim, 500/self.map.xdim), 1 )

    # marker_size needs to be roughly plot.bounds[0] / (xdim*2)
    plot = ScatterPlot(index = x_ds, value = y_ds,
                       index_mapper = LinearMapper(range = x_dr),
                       value_mapper = LinearMapper(range = y_dr),
                       color = "black", bgcolor = "white", 
                       marker = "square", marker_size = markersize)

    plot.aspect_ratio = float(self.xdim) / float(self.ydim)

    pgx = PlotGrid(component = plot, mapper = plot.index_mapper, orientation = 'vertical',
                   grid_interval = 1, line_width = 1.0, line_style = "dot", line_color = "lightgray")
    pgy = PlotGrid(component = plot, mapper = plot.value_mapper, orientation = 'horizontal',
                   grid_interval = 1, line_width = 1.0, line_style = "dot", line_color = "lightgray")
    plot.underlays.append(pgx)
    plot.underlays.append(pgy)
    add_default_axes(plot)

    # this is meaningless until we're actually rendered
    #print plot.bounds

    return plot    

