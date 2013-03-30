#!/usr/bin/python

from particles import *
from particleplot import *

from robot import *
from robotplot import *

from map import *
from mapplot import *

#from probability import *

from traits.api import String, Button
from traitsui.api import InstanceEditor
from chaco.api import OverlayPlotContainer

import argparse
from numpy.random import random

import std_sensors
import std_noise

noise_params = std_noise.noise_params

particle_count = None
map = None

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
                       Group(Item('actual'), Item('guess'),Item('score',springy=True), orientation = 'horizontal'),
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
      measured = self.robot.sense(map)
      self.sensors = "F: %0.2f  L: %0.2f  R: %0.2f  B: %0.2f" % ( measured[0], measured[1], measured[2], measured[3])

    # currently not used, logic wrapped into move_fired for now
    def _update_fired(self):
      print "update!"
      measured = self.robot.sense(map)
      self.sensors = "F: %0.2f  L: %0.2f  R: %0.2f  B: %0.2f" % ( measured[0], measured[1], measured[2], measured[3])
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

    def __init__(self):
      m = MapPlot(map = map)
      self.map_scale = map.scale
      self.map_info = "%s" % map

      self.noise_sensor = std_sensors.default[0].noise
      self.noise_move = noise_params['move']
      self.noise_turn = noise_params['turn']

      start_pose = Pose(map.x_inches/2, map.y_inches/2, 0.0)
      robot = SimRobot(start_pose, std_sensors.centered_cone, noise_params = noise_params)
      rplotter = RobotPlotter(robot = robot, xsize = map.x_inches, ysize = map.y_inches)

      localizer = ParticleLocalizer(std_sensors.centered_cone, noise_params, map, particle_count, start_pose)
      pplotter = ParticlePlotter(particles = localizer.p, xsize = map.x_inches, ysize = map.y_inches, color = 'red')

      guessbot = Robot(start_pose)
      guessplotter = RobotPlotter(robot = guessbot, xsize = map.x_inches, ysize = map.y_inches, color = 'green' )

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

  map = Map(args.map, args.res)
  particle_count = args.num

  print map
  #print map.data

  s = Simulator()
  s.configure_traits()
