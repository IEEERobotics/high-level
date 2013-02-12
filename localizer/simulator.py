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

particle_count = 100

class Container(HasTraits):
    container = Instance(OverlayPlotContainer)
    robot = DelegatesTo('rplot')   # assigned during init
    output = String('Push the button!')
    sense = Button()
    update = Button()
    move = Button()
    move_theta = Float(0.5)
    move_dist = Float(0.5)
    
    particle_count = Int(100)  # not yet used
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

    def _move_fired(self):
      print "Move!"
      self.robot.move(self.move_theta, self.move_dist)
      self.particles.move(self.move_theta, self.move_dist)

      # do we want to resample every move?
      measured = self.robot.sense_all(map2d)
      self.particles.sense_all(map2d)
      self.particles.resample(measured)

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
        rplot = RobotPlot(robot = robot)
        self.particles = ParticlePlotter(robot = robot, n = particle_count)
        m = MapPlot(mapdata = map2d)
        c = OverlayPlotContainer()
        c.add(m.plot)
        c.add(self.particles.qplot)
        c.add(rplot.plot)
        self.container = c
        self.rplot = rplot

if __name__ == "__main__":
    map2d = [[1,1,1,1,1,1,1,1,1,1,1,1],
          [1,0,0,0,0,0,0,0,0,0,0,1],
          [1,0,1,1,0,0,0,0,0,0,0,1],
          [1,0,1,1,0,0,0,0,0,0,0,1],
          [1,0,0,0,0,0,0,0,0,0,0,1],
          [1,0,0,0,0,0,0,0,0,0,0,1],
          [1,0,0,0,0,0,0,1,1,1,1,1],
          [1,0,0,0,0,0,0,0,0,0,0,1],
          [1,0,0,0,0,0,0,0,0,0,0,1],
          [1,1,1,1,1,1,1,1,1,1,1,1]]
    map2d.reverse()

    c = Container()
    c.configure_traits()
