#!/usr/bin/python

from pylab import *

from raycast import *

x1 = 1.3
y1 = 1.9
dist = 8
theta = pi/6
x2 = x1 + dist*cos(theta)
y2 = y1 + dist*sin(theta)

clf()
# actual line of sight
plot([x1, x2],[y1,y2], color ='blue')

# grid limited estimates
x1 = int(x1+0.5)
y1 = int(y1+0.5)
x2 = int(x2+0.5)
y2 = int(y2+0.5)
scatter([x1+0.5,x2+0.5],[y1+0.5,y2+0.5], color='green', marker='o')

plot([x1+0.5, x2+0.5],[y1+0.5,y2+0.5], color = 'red')
l = raytrace(x1,y1,x2,y2)
scatter(l[0],l[1], color='red')
scatter(floor(l[0])+0.5,floor(l[1])+0.5, marker='s', s=20**2, color='red')

grid(True)

ax = gca()
ax.set_xticks(arange(0,12,1))
ax.set_yticks(arange(0,12,1))
axis('equal')
show()
