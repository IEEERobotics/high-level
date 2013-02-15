#!/usr/bin/python

from traits.api import HasTraits, Instance, Array, Property, Int
from traitsui.api import View, Item
from chaco.api import ScatterPlot, ArrayDataSource, DataRange1D, LinearMapper, \
                  add_default_axes, PlotGrid
from enable.api import ComponentEditor, Component
from numpy import array

import csv

# loads map into 2d list:
#   [y][x] are map coordinates
#   [0][0] is bottom left corner
class Map():
  def __init__(self, filename):
    data = list( csv.reader(open(filename, 'r')))
    data = [ [int(x) for x in y] for y in data  ]  # convert string to ints
    data.reverse()
    self.data = data

  @property
  def xdim(self):
    return len(self.data[0])
  @property
  def ydim(self):
    return len(self.data)
  def __str__(self):
    return "Map: (%d, %d)" % (self.xdim, self.ydim)

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

    self.data = self.map.data
    data_xy = []
    for y in range(len(self.data)):
      for x in range(len(self.data[y])):
        #if self.data[ (len(self.data)-1) - y][x] == 1:
        if self.data[y][x] == 1:
          data_xy.append([x,y])

    data_xy = array(data_xy)

    x_ds = ArrayDataSource(data_xy[:,0])
    y_ds = ArrayDataSource(data_xy[:,1])
    x_dr = DataRange1D(x_ds)
    y_dr = DataRange1D(y_ds)

    # marker_size needs to be roughly plot.bounds[0] / (xdim*2)
    plot = ScatterPlot(index = x_ds, value = y_ds,
                       index_mapper = LinearMapper(range = x_dr),
                       value_mapper = LinearMapper(range = y_dr),
                       color = "black", bgcolor = "white", 
                       marker = "square", marker_size = 400 / len(self.data))

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

