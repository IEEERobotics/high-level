# TOOD:
# add textbox item
# add sense and update buttons

from particles import *
from robot import *
from map import *
from probability import *

from traits.api import String, Button
from traitsui.api import InstanceEditor
from chaco.api import OverlayPlotContainer

import argparse

particle_count = None
map = None

class Simulator(HasTraits):
    container = Instance(OverlayPlotContainer)
    robot = DelegatesTo('rplotter')   # assigned during init
    robot_guess = DelegatesTo('rgplotter', 'robot')   # assigned during init
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
      measured = self.robot.sense_all(map2d)
      self.output = "F: %0.2f  L: %0.2f  R: %0.2f" % ( measured[0], measured[1], measured[2])

    # currently not used, logic wrapped into move_fired for now
    def _update_fired(self):
      print "update!"
      measured = self.robot.sense_all(map)
      self.particles.sense_all(map)
      self.particles.resample(measured)

      x, y, theta = self.particles.guess()
      self.output = "Guess: X: %0.2f Y: %0.2f: Theta: %0.2f" % (x,y,theta)
      self.robot_guess.x = x
      self.robot_guess.y = y
      self.robot_guess.theta = theta

    def _move_fired(self):
      print "Move!"
      self.robot.move(self.move_theta, self.move_dist)
      self.particles.move(self.move_theta, self.move_dist)
      self.rplotter.do_redraw()

      # do we want to resample every move?
      self._update_fired() 
      self.pplotter.do_redraw()
      self.rgplotter.do_redraw()

    def __init__(self):
      m = MapPlot(map = map)

      robot = Robot(x = map.xdim/2, y = map.ydim/2, theta = 0.0, color = 'red')
      rplotter = RobotPlotter(robot = robot, xsize = m.xdim, ysize = m.ydim)
      particles = Particles(robot, map, particle_count) 
      pplotter = ParticlePlotter(robot = robot, particles = particles, xsize = m.xdim, ysize = m.ydim)
      print particles

      rg = Robot(x = m.xdim/2, y = m.ydim/2, theta = 0.0, color = 'green')
      rgplotter = RobotPlotter(robot = rg, xsize = m.xdim, ysize = m.ydim )

      c = OverlayPlotContainer()
      c.add(m.plot)
      c.add(pplotter.qplot)
      c.add(rgplotter.plot)
      c.add(rplotter.plot)

      self.container = c
      self.pplotter = pplotter
      self.rplotter = rplotter
      self.rgplotter = rgplotter

if __name__ == "__main__":

  parser = argparse.ArgumentParser(description='Localization simulator')
  parser.add_argument('-m', '--map', help='Map file', default='test.map' )
  parser.add_argument('-n', '--num', help='Number of partiles', type=int, default='500' )
  args = parser.parse_args()

  map = Map(args.map)
  particle_count = args.num

  print map

  s = Simulator()
  s.configure_traits()
