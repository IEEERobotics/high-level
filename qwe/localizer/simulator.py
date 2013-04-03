#!/usr/bin/python

from particles import *
from particleplot import *

from robot import *
from robotplot import *

#from map import *
import map
from mapplot import *

#from probability import *

from traits.api import String, Button
from traitsui.api import InstanceEditor
from chaco.api import OverlayPlotContainer

import argparse
from numpy.random import random

import std_sensors
import std_noise

import sys
sys.path.append('..')
import mapping.map_class
sys.modules['map_class'] = mapping.map_class  # deal with the fact we pickled a module in another dir
import mapping.pickler

import logging.config
logging.config.fileConfig('logging.conf')  # local version
logger = logging.getLogger(__name__)

noise_params = std_noise.noise_params

#particle_count = None
#map = None

class Simulator(HasTraits):
    container = Instance(OverlayPlotContainer)
    robot = DelegatesTo('rplotter')   # assigned during init
    robot_guess = DelegatesTo('guessplotter', 'robot')   # assigned during init
    particles = DelegatesTo('pplotter')   # assigned during init

    sensors = String('')
    actual = String('')
    guess = String('')
    score = Float('0.0')

    map_info = String('')
    map_scale = Float('1.0')

    sense = Button()
    update = Button()
    move = Button()
    random = Button()
    move_theta = Float(0.5)
    move_dist = Float(0.5)
    
    particle_count = Int(10)  # not yet used
    noise_sensor = Float(0.0)
    noise_move = Float(0.0)
    noise_turn = Float(0.0)

    traits_view = View(
                       #Item('robot', editor=InstanceEditor(), style='custom'),
                       Item('container', editor=ComponentEditor(), show_label=False),
                       Group(Item('actual',springy=True), Item('guess', springy=True),Item('score',springy=True), orientation = 'horizontal'),
                       Group(Item('sense'),Item('update'), orientation = 'horizontal'),
                       Group(Item('random'), 
                             Item('move'),
                             Item('move_theta'),
                             Item('move_dist'),
                             orientation = 'horizontal'),
                       Group(Item('map_info', springy=True), Item('map_scale'), orientation = 'horizontal'),
                       Group(Item('noise_sensor'), Item('noise_move'), 
                             Item('noise_turn'), orientation = 'horizontal'),
                       Item('sensors')

        )

    def _sense_fired(self):
      measured = self.robot.sense(themap)
      out = ""
      for name,val in measured.items():
        out += "%s: %s " % (name, val)
      self.sensors = out

    # currently not used, logic wrapped into move_fired for now
    def _update_fired(self):
      print "update!"
      measured = self.robot.sense(themap)
      out = ""
      for name,val in measured.items():
        out += "%s: %s " % (name, val)
      self.sensors = out
      self.localizer.update(measured)

      guess = self.localizer.guess()
      self.guess = "%s" % guess
      self.robot_guess.pose = guess
      self.score = self.localizer.score()
      print

    def _random_fired(self):
      print "Random move!"
      self.move_dist = random() * 10 
      self.move_theta = random() * pi - pi/2
      self._move_fired()

    def _move_fired(self):
      print "Move!"
      self.robot.move(self.move_theta, self.move_dist)
      self.actual = "%s" % self.robot
      self.localizer.move(self.move_theta, self.move_dist)
      self.rplotter.do_redraw()

      # do we want to resample every move?
      self._update_fired() 
      self.pplotter.do_redraw()
      self.guessplotter.do_redraw()

    def __init__(self, sensors = std_sensors.offset_str):
      m = MapPlot(map = themap)
      self.map_scale = themap.scale
      self.map_info = "%s" % themap

      self.noise_sensor = std_sensors.ultra_noise
      self.noise_move = noise_params['move']
      self.noise_turn = noise_params['turn']

      #start_pose = Pose(themap.x_inches/2, themap.y_inches/2, 0.0)
      start_pose = Pose(6, 2.6, pi/2)
      robot = SimRobot(start_pose, sensors, noise_params = noise_params)
      rplotter = RobotPlotter(robot = robot, xsize = themap.x_inches, ysize = themap.y_inches)

      localizer = ParticleLocalizer(sensors, noise_params, themap, particle_count, start_pose, logger = logger)
      pplotter = ParticlePlotter(particles = localizer.p, xsize = themap.x_inches, ysize = themap.y_inches, color = 'red')

      guessbot = Robot(start_pose)
      guessplotter = RobotPlotter(robot = guessbot, xsize = themap.x_inches, ysize = themap.y_inches, color = 'green' )

      c = OverlayPlotContainer()
      c.add(m.plot)
      c.add(pplotter.qplot)
      c.add(guessplotter.plot)
      c.add(rplotter.plot)

      self.container = c
      self.pplotter = pplotter
      self.rplotter = rplotter
      self.guessplotter = guessplotter

      self.localizer = localizer

if __name__ == "__main__":

  parser = argparse.ArgumentParser(description='Localization simulator')
  parser.add_argument('-m', '--map', help='Map file', default='maps/test.map' )
  parser.add_argument('-n', '--num', help='Number of partiles', type=int, default='500' )
  parser.add_argument('-r', '--res', help='Map res (inchs/block)', type=float, default='1.0' )
  args = parser.parse_args()

  #map = Map(args.map, args.res)
  map_obj = mapping.pickler.unpickle_map('../mapping/map.pkl')
  waypoints = mapping.pickler.unpickle_waypoints('../mapping/waypoints.pkl')
  for i in range(14):
    map_obj.fillLoc(waypoints, "St%02d"%(i+1), {'desc':8})
  #for i in range(6):
  #  map_obj.fillLoc(waypoints, "L%02d"%(i+1), {'desc':8})
  #for i in range(6):
  #  map_obj.fillLoc(waypoints, "Se%02d"%(i+1), {'desc':8})

  themap = map.Map.from_map_class(map_obj)

  particle_count = args.num

  print themap
  #print map.data

  s = Simulator()
  s.configure_traits()
