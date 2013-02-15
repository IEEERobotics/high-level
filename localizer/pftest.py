import robot, particles, map
from numpy import *

num = 1500

startx = 6
starty = 5

m = map.Map('test3.map')
r = robot.Robot(x = startx, y = starty, theta = 0, 
                noise_move = 0.1, noise_turn = 0.2, noise_sense = 0.25)
p = particles.Particles(r, m, num)
ideal = robot.Robot(x = startx, y = starty, theta = 0, 
                    noise_move = 0.0, noise_turn = 0.0, noise_sense = 0.0)

print "Start: (%0.2f, %0.2f) @ %+0.2f" % (r.x, r.y, r.theta)
print

for i in range(1,20):
  turn = random.random() * pi - pi/2
  move = random.random()
  print "Turn: %+0.2f, Move: %0.2f" % (turn, move)
  r.move(turn, move)
  ideal.move(turn, move)
  p.move(turn, move)
  print "Ideal: (%0.2f, %0.2f) @ %+0.2f" % (ideal.x, ideal.y, ideal.theta)
  print "Robot: (%0.2f, %0.2f) @ %+0.2f" % (r.x, r.y, r.theta)
  s = r.sense_all(m)
  p.sense_all(m)
  p.resample(s)
  print "Guess: (%0.2f, %0.2f) @ %+0.2f" % p.guess()
  print
