#!/usr/bin/python

from pylab import *
from raycast import *
from map import *

clf()
m = Map('maps/test2.map', 0.25)
scatter(m.xy()[:,0],m.xy()[:,1], color='black', marker='s', s=25**2)

def plot_los(x1,y1,theta,dist):
  x2 = x1 + dist*cos(theta)
  y2 = y1 + dist*sin(theta)

  # actual line of sight
  scatter(x1,y1, color='blue', marker='o', s=10**2)
  plot([x1, x2],[y1,y2], color ='blue', lw=2)
  x1 = int(x1)
  y1 = int(y1)
  x2 = int(x2)
  y2 = int(y2)

  plot([x1+0.5, x2+0.5],[y1+0.5,y2+0.5], color = 'red', lw=2)
  wx,wy = raywall(x1,y1,x2,y2,m)

  scatter(wx+0.5,wy+0.5, color='red', marker='s', s=20**2)

  return wx,wy

######################

dist = 15

plot_los(1.3,1.9,pi/2,dist)
print find_wall(1.3*m.scale,1.9*m.scale,pi/2,dist*m.scale,m)

plot_los(5.5,6.3,pi/6,dist)
print find_wall(5.5*m.scale,6.3*m.scale,pi/6,dist*m.scale,m)

plot_los(14.9,3.5,-2*pi/3,dist)
print find_wall(14.9*m.scale,3.5*m.scale,-2*pi/3,dist*m.scale,m)

grid(True)
ax = gca()
ax.set_xticks(arange(0,m.xdim,1))
ax.set_yticks(arange(0,m.ydim,1))
axis('equal')

show()
