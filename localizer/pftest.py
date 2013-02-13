import robot, particles, map
import numpy

num = 10 

r = robot.Robot(x = 6, y = 5, theta = 0)
p = particles.Particles(r, num)
m = map.loadmap('test.map')

s = r.sense_all(m)
p.sense_all(m)
p.resample(s)

