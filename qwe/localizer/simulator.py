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
    output = String('Push some buttons!')
    sense = Button()
    update = Button()
    move = Button()
    move_theta = Float(0.5)
    move_dist = Float(0.5)
    
    particle_count = Int(10)  # not yet used
    noise_sensor = Float(0.5)
    noise_forward = Float(0.5)
    noise_turn = Float(0.1)

    traits_view = View(
                       #Item('robot', editor=InstanceEditor(), style='custom'),
                       Item('container', editor=ComponentEditor(), show_label=False),
                       Item('output'),
                       Group(Item('sense'),Item('update'), orientation = 'horizontal'),
                       Group(Item('move'),
                             Item('move_theta'),
                             Item('move_dist'),
                             orientation = 'horizontal'),
                       Group(Item('noise_sensor'), Item('noise_forward'), 
                             Item('noise_turn'), orientation = 'horizontal')
        )

    def _sense_fired(self):
      measured = self.robot.sense(map)
      self.output = "F: %0.2f  L: %0.2f  R: %0.2f" % ( measured[0], measured[1], measured[2])

    # currently not used, logic wrapped into move_fired for now
    def _update_fired(self):
      print "update!"
      measured = self.robot.sense(map)
      self.localizer.update(measured)

      guess = self.localizer.guess()
      self.output = "Guess: %s" % guess
      self.robot_guess.pose = guess

    def _move_fired(self):
      print "Move!"
      self.robot.move(self.move_theta, self.move_dist)
      self.localizer.move(self.move_theta, self.move_dist)
      self.rplotter.do_redraw()

      # do we want to resample every move?
      self._update_fired() 
      self.pplotter.do_redraw()
      self.guessplotter.do_redraw()

    def __init__(self):
      m = MapPlot(map = map)

      start_pose = Pose(map.xdim/2, map.ydim/2, 0.0)
      robot = SimRobot(start_pose, std_sensors.sensors, noise_params = noise_params)
      rplotter = RobotPlotter(robot = robot, xsize = m.xdim, ysize = m.ydim)
      localizer = ParticleLocalizer(std_sensors.sensors, noise_params, map, particle_count)
      pplotter = ParticlePlotter(particles = localizer.p, xsize = m.xdim, ysize = m.ydim, color = 'red')

      guessbot = Robot(start_pose)
      guessplotter = RobotPlotter(robot = guessbot, xsize = m.xdim, ysize = m.ydim, color = 'green' )

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
  args = parser.parse_args()

  map = Map(args.map)
  particle_count = args.num

  print map
  #print map.data

  s = Simulator()
  s.configure_traits()
