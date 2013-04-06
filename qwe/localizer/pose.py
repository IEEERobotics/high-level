from numpy import sin,cos,pi

class Pose(object):

  def __init__(self, x, y, theta):
    self.x = x
    self.y = y
    self.theta = theta

  @property
  def v(self):
    return cos(self.theta), sin(self.theta)

  @property
  def xy(self):
    return self.x,self.y

  def offset(self, x,y,theta):
    o = self.copy()
    o.x +=  x * cos(self.theta)
    o.x += -y * sin(self.theta)

    o.y += x * sin(self.theta)
    o.y += y * cos(self.theta)

    o.theta = (o.theta + theta) % (2*pi) 
    return o

  def copy(self):
    return Pose(self.x, self.y, self.theta)

  def __add__(self, p):
    return Pose(self.x + p.x, self.y + p.y, (self.theta + p.theta) % (2*pi))

  def __str__(self):
    return "(%0.2f, %0.2f) @ %+0.2f" % (self.x, self.y, self.theta)

  def __repr__(self):
    return "<Pose: (%0.2f, %0.2f) @ %+0.2f>" % (self.x, self.y, self.theta)
