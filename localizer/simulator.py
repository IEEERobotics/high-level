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

class Container(HasTraits):
    container = Instance(OverlayPlotContainer)
    robot = DelegatesTo('rplot')   # assigned during init
    output = String('Push the button!')
    sense = Button()
    update = Button()
    move = Button()
    move_theta = Float()
    move_dist = Float(1.0)

    def _sense_fired(self):
      sense = self.robot.sense(map2d)
      self.output = "Sensed: " + str(sense)

    def _update_fired(self):
      print "update!"
      measured = self.robot.sense(map2d)
      self.particles.sense(map2d)
      self.particles.resample(measured)

    def _move_fired(self):
      print "Move!"
      self.robot.move(self.move_theta, self.move_dist)
      self.particles.move(self.move_theta, self.move_dist)

      # do we want to resample every move?
      measured = self.robot.sense(map2d)
      self.particles.sense(map2d)
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
                             orientation = 'horizontal')
        )

    def __init__(self):
        self.particles = ParticlePlotter()
        robot = Robot(x = 5.0, y = 5.0, theta = 0.0)
        rplot = RobotPlot(robot = robot)
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
