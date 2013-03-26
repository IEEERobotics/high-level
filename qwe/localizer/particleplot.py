# Enthought library imports
from enable.api import Component, ComponentEditor
from traits.api import HasTraits, Instance, Property, Int, Float, Array, Range, cached_property
from traitsui.api import Item, View, Group

# Chaco imports
from chaco.api import ArrayDataSource, MultiArrayDataSource, DataRange1D, \
        LinearMapper, QuiverPlot, Plot, ArrayPlotData

from particles import *

size = (100, 100)

class ParticlePlotter(HasTraits):

    qplot = Instance(QuiverPlot)
    vsize = Int(10)
 
    # field dimensions, should we just hook in the map object and use it's values directly?
    xsize = Float
    ysize = Float

    particles = Instance(Particles)
   
    xs = ArrayDataSource()
    ys = ArrayDataSource()
    vector_ds = MultiArrayDataSource()

    # this defines the default view when configure_traits is called
    traits_view = View(Item('qplot', editor=ComponentEditor(size=size), show_label=False),
                       Item('vsize'), 
                       resizable=True)

    def do_redraw(self):
      self.xs.set_data(self.particles.x, sort_order='ascending')
      self.ys.set_data(self.particles.y)
      self.vector_ds.set_data(self.vectors)

    # magic function called when vsize trait is changed
    def _vsize_changed(self):
      #print "vsize is: ", self.vsize
      #self.vectors = array( zip(self.vsize*cos(self.theta), self.vsize*sin(self.theta)) )
      self.vector_ds.set_data(self.vectors)
      #print self.vector_ds.get_shape()
      self.qplot.request_redraw()
        
    #@cached_property
    @property
    def vectors(self):
      return self.particles.v * self.vsize

    # ?? dynamic instantiation of qplot verus setting up in init?
    #  robot param is the robot we are modeling -- source of params
    def _qplot_default(self):

      # Force an update of the array data sources so changes are plotted
      self.xs.set_data(self.particles.x, sort_order='ascending')
      self.ys.set_data(self.particles.y)

      #self.vector_ds = MultiArrayDataSource(self.vectors)
      self.vector_ds.set_data(self.vectors)

      # Set up the Plot
      xrange = DataRange1D()
      xrange.add(self.xs)
      xrange.set_bounds(0,self.xsize)
      yrange = DataRange1D()
      yrange.add(self.ys)
      yrange.set_bounds(0,self.ysize)
      qplot = QuiverPlot(index = self.xs, value = self.ys,
                      vectors = self.vector_ds,
                      #data_type = 'radial',  # not implemented
                      index_mapper = LinearMapper(range=xrange),
                      value_mapper = LinearMapper(range=yrange),
                      bgcolor = "white", line_color = "grey")

      qplot.aspect_ratio = float(self.xsize) / float(self.ysize)
      return qplot

if __name__ == "__main__":
    ParticlePlotter().configure_traits()
