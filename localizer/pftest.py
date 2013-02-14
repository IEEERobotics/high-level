import robot, particles, map
from numpy import *

num = 1000

m = map.loadmap('test2.map')
r = robot.Robot(x = 6, y = 5, theta = 0)
p = particles.Particles(r, m, num)

print "Start: (%0.2f, %0.2f) @ %+0.2f" % (r.x, r.y, r.theta)
print

for i in range(1,15):
  turn = random.random() * pi - pi/2
  move = random.random()
  r.move(turn, move)
  p.move(turn, move)
  print "Robot: (%0.2f, %0.2f) @ %+0.2f" % (r.x, r.y, r.theta)
  s = r.sense_all(m)
  p.sense_all(m)
  p.resample(s)
  print "Guess: (%0.2f, %0.2f) @ %+0.2f" % p.guess()
  print
