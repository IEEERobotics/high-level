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

particle_count = 500

class Container(HasTraits):
    container = Instance(OverlayPlotContainer)
    robot = DelegatesTo('rplotter')   # assigned during init
    particles = DelegatesTo('pplotter')   # assigned during init
    output = String('Push the button!')
    sense = Button()
    update = Button()
    move = Button()
    move_theta = Float(0.5)
    move_dist = Float(0.5)
    
    particle_count = Int(10)  # not yet used
    noise_sensor = Float(0.5)
    noise_forward = Float(0.5)
    noise_turn = Float(0.1)

    def _sense_fired(self):
      measured = self.robot.sense_all(map2d)
      self.output = "F: %0.2f  L: %0.2f  R: %0.2f" % ( measured[0], measured[1], measured[2])

    # currently not used, logic wrapped into move_fired for now
    def _update_fired(self):
      print "update!"
      measured = self.robot.sense_all(map2d)
      self.particles.sense_all(map2d)
      self.particles.resample(measured)
      x = self.particles.x.mean()
      y = self.particles.y.mean()
      theta = self.particles.theta.mean()  # TODO: average individual vector components NOT theta!
      self.output = "Guess: X: %0.2f Y: %0.2f: Theta: %0.2f" % (x,y,theta)

    def _move_fired(self):
      print "Move!"
      self.robot.move(self.move_theta, self.move_dist)
      self.particles.move(self.move_theta, self.move_dist)

      # do we want to resample every move?
      self._update_fired() 
      #measured = self.robot.sense_all(map2d)
      #self.particles.sense_all(map2d)
      #self.particles.resample(measured)

      self.pplotter.do_redraw()

    traits_view = View(
                       Item('robot', editor=InstanceEditor(), style='custom'),
                       Item('container', editor=ComponentEditor(), show_label=False),
                       Item('output'),
                       Item('sense'),
                       Item('update'),
                       Group(Item('move'),
                             Item('move_theta'),
                             Item('move_dist'),
                             orientation = 'horizontal'),
                       Group(Item('noise_sensor'), Item('noise_forward'), Item('noise_turn'))
        )

    def __init__(self):
        robot = Robot(x = 6.0, y = 5.0, theta = 0.0)
        rplotter = RobotPlotter(robot = robot)
        particles = Particles(robot, particle_count)
        pplotter = ParticlePlotter(robot = robot, particles = particles)
        m = MapPlot(mapdata = map2d)

        c = OverlayPlotContainer()
        c.add(m.plot)
        c.add(pplotter.qplot)
        c.add(rplotter.plot)

        self.container = c
        self.pplotter = pplotter
        self.rplotter = rplotter

if __name__ == "__main__":

  map2d = loadmap('test.map')

  c = Container()
  c.configure_traits()
