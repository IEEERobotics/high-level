#!/usr/bin/python

# Major library imports
from numpy import array, sort, pi, cos, sin, zeros
from numpy.random import random

# Enthought library imports
from enable.api import Component, ComponentEditor
from traits.api import HasTraits, Instance, Property, Int, Array, Range, cached_property
from traitsui.api import Item, View, Group

# Chaco imports
from chaco.api import ArrayDataSource, MultiArrayDataSource, DataRange1D, \
        LinearMapper, QuiverPlot, Plot, ArrayPlotData

# for sense 
from raycast import wall
from numpy.linalg import norm
from probability import gaussian 
from random import gauss  

from robot import *

size = (100, 100)

class ParticlePlotter(HasTraits):

    qplot = Instance(QuiverPlot)
    #vsize = Range(low = -20.0, high = 20.0, value = 1.0)
    vsize = Int(10)

    # the associated robot object which our particles are simulating
    #   provides: x,y range and sensors list
    robot = Instance(Robot)
    
    numpts = 0  # set in init
    theta = Array
    vectors = Property(Array, depends_on=["vsize", "theta"])
    vector_ds = MultiArrayDataSource()

    prob = Array    # probability measurement, "weight"
    sensed = []

    # this defines the default view when configure_traits is called
    traits_view = View(Item('qplot', editor=ComponentEditor(size=size), show_label=False),
                       Item('vsize'), 
                       resizable=True)

    def __init__(self, robot, n = 100):
      # need to move the logic out of the GUI class and into its own particles class
      self.numpts = n
      self.sensed = zeros((robot.num_sensors,self.numpts))  # modeled sensor data
      self.robot = robot


    # update particles based on movement model, predicting new pose
    #   ? how do we handle moving off map?  or into any wall?
    def move(self, dtheta, forward):
      x = self.qplot.index.get_data()
      y = self.qplot.value.get_data()
      theta = self.theta
      for i in range(self.numpts):
        theta[i] = ( (theta[i] + dtheta + pi) % (2*pi) ) - pi
        theta[i] = gauss(theta[i], 0.1 * dtheta)
        dx = forward * cos(theta[i])
        dy = forward * sin(theta[i])
        x[i] += dx
        y[i] += dy
        x[i] = gauss(x[i], 0.1 * dx)
        y[i] = gauss(y[i], 0.1 * dy)

      # quick and dirty, keep things in range
      #  at the very least the max bounds need to be parameters
      x.clip(0,11.0)
      y.clip(0,9.0)

      self.qplot.index.set_data(x)
      self.qplot.value.set_data(y)
      #self.theta = theta  # for notification?
      #print self.vectors
      self.vector_ds.set_data(self.vectors)
      self.qplot.request_redraw()
      
    def sense(self, rel_theta, mapdata):
      x = self.qplot.index.get_data()
      y = self.qplot.value.get_data()
      data = zeros(self.numpts)
      #print "rel theta: ", rel_theta
      sense_theta = [ ((t + pi + rel_theta) % (2*pi) - pi) for t in self.theta]
      #print "Thetas: ",
      #print " ".join(["%0.2f" % s for s in sense_theta])
      for i in range(self.numpts):
        # the logic here is currently a duplicate of that for robot.sense(), but in 
        #   reality, robot.sense() will pull actual sensor data from the sensors (not a model)
        wx,wy = wall(x[i],y[i],sense_theta[i],mapdata)
        # add gaussian noise to (otherwise exact) distance calculation?
        data[i] = norm( [x[i]-wx, y[i]-wy] )
      return data

    def sense_all(self, mapdata):
      x = self.qplot.index.get_data()
      y = self.qplot.value.get_data()
      for s in self.robot.sensors:
        # get the full set of particle senses for this sensor
        self.sensed[s.index] = self.sense(s.angle, mapdata)
      for i in range(self.numpts):
        print "  %0.2f, %0.2f @ %0.2f = " % (x[i], y[i], self.theta[i]),
        print ", ".join( [ "%s: %0.2f" % (s.name, self.sensed[s.index,i]) for s in self.robot.sensors ])

    # Currently assumes self.sensed and measured have both been updated
    def resample(self, measured):
      x = self.qplot.index.get_data()
      y = self.qplot.value.get_data()
      theta = self.theta
      print "Updating particle weights:"
      # create an array of particle weights to use as resampling probability
      for i in range(self.numpts):
        self.prob[i] = 1.0
        for s in self.robot.sensors:
          # compare measured input of sensor versus the particle's value, adjusting prob accordingly
          #   TODO: refine 1.0 noise parameter to something meaningful
          self.prob[i] *= gaussian(self.sensed[s.index][i], 1.0, measured[s.index])
        print "  %0.2f, %0.2f @ %0.2f = %0.2e" % (x[i], y[i], theta[i], self.prob[i]) 

      # resample (x, y, theta) using wheel resampler
      new = []
      step = max(self.prob) * 2.0
      cur = int(random() * self.numpts)
      beta = 0.0
      for i in range(self.numpts):
        beta += random() * step  # 0 - step size
        while beta > self.prob[cur]:
          beta -= self.prob[cur]
          cur = (cur+1) % self.numpts
          #print "b: %0.2f, cur: %d, prob = %0.2f" % (beta, cur, self.prob[cur])
        new.append((x[cur], y[cur], theta[cur], self.prob[cur]))
      print "Resampled:"
      for i in range(self.numpts):
        print "  %0.2f, %0.2f @ %+0.2f = " % (x[i], y[i], self.theta[i]),
        print ", ".join( [ "%s: %0.2f" % (s.name, self.sensed[s.index,i]) for s in self.robot.sensors ])
      self.qplot.index.set_data( [e[0] for e in new] )
      self.qplot.value.set_data( [e[1] for e in new] )
      self.theta = [e[2] for e in new]
      self.vector_ds.set_data(self.vectors)
      self.qplot.request_redraw()


     


    # magic function called when vsize trait is changed
    def _vsize_changed(self):
      #print "vsize is: ", self.vsize
      #self.vectors = array( zip(self.vsize*cos(self.theta), self.vsize*sin(self.theta)) )
      self.vector_ds.set_data(self.vectors)
      #print self.vector_ds.get_shape()
      self.qplot.request_redraw()
        
    def _theta_default(self):
      return random(self.numpts)*2*pi

    def _sensed_default(self):
      return zeros(self.numpts)

    def _prob_default(self):
      return zeros(self.numpts)

    #@cached_property
    def _get_vectors(self):
      return array( zip(cos(self.theta), sin(self.theta)) ) * self.vsize

    # ?? dynamic instantiation of qplot verus setting up in init?
    #  robot param is the robot we are modeling -- source of params
    def _qplot_default(self):

      xsize = self.robot.xmax
      ysize = self.robot.ymax

      # Create starting points for the vectors.
      x = sort(random(self.numpts)) * xsize # sorted for axis tick calculation?
      y = random(self.numpts) * ysize

      # Create an array data sources to plot all vectors at once
      xs = ArrayDataSource(x, sort_order='ascending')
      ys = ArrayDataSource(y)

      #self.vector_ds = MultiArrayDataSource(self.vectors)
      self.vector_ds.set_data(self.vectors)

      # Set up the Plot
      xrange = DataRange1D()
      xrange.add(xs)
      xrange.set_bounds(0,xsize)
      yrange = DataRange1D()
      yrange.add(ys)
      yrange.set_bounds(0,ysize)
      qplot = QuiverPlot(index = xs, value = ys,
                      vectors = self.vector_ds,
                      #data_type = 'radial',  # not implemented
                      index_mapper = LinearMapper(range=xrange),
                      value_mapper = LinearMapper(range=yrange),
                      bgcolor = "white")

      qplot.aspect_ratio = xsize / ysize
      return qplot

if __name__ == "__main__":
    ParticlePlotter().configure_traits()
