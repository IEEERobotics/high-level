from numpy import clip, sin, cos, sign
from numpy.linalg import norm

testmap = [[1,1,1,1,1,1,1,1,1,1,1,1],
          [1,0,0,0,0,0,0,0,0,0,0,1],
          [1,0,0,0,0,0,0,0,0,0,0,1],
          [1,0,0,0,0,0,0,0,0,0,0,1],
          [1,0,0,0,0,0,0,0,0,0,0,1],
          [1,0,0,0,0,0,0,0,0,0,0,1],
          [1,0,0,0,0,0,0,0,0,0,0,1],
          [1,0,0,0,0,0,0,0,0,0,0,1],
          [1,0,0,0,0,0,0,0,0,0,0,1],
          [1,1,1,1,1,1,1,1,1,1,1,1]]
testmap.reverse()


def calc_line(x,y,theta,mapx,mapy):
  maxlen = norm([mapy,mapx])
  xoff = int(x + maxlen * cos(theta))
  yoff = int(y + maxlen * sin(theta))
  x = clip(x,0,mapx-1)
  y = clip(y,0,mapy-1)
  return bresen(x,y,xoff,yoff)

def wall(x,y,theta,mapdata):
  mapy = len(mapdata)
  mapx = len(mapdata[0])
  xpath,ypath = calc_line(x,y,theta,mapx,mapy)
  for i in range(len(xpath)):
    if mapdata[ypath[i]][xpath[i]] == 1:
      return xpath[i],ypath[i]
  return -1,-1

def bresen(x0,y0, x1, y1):

  xdata = []
  ydata = []
 
  # TODO: use the subpixel value instead of ints
  x0 = int(x0)
  y0 = int(y0)

  dx = x1 - x0
  dy = y1 - y0
  xmod = sign(dx)
  ymod = sign(dy)
  dx = abs(dx)
  dy =abs(dy)

  # algorithm assumes dx >= dy, so swap if necessary
  if( dx < dy ):
    ydata,xdata = bresen(y0,x0,y1,x1)
    return xdata,ydata

  # TODO: preset this error term based on subpixel offset instead
  D = 2*dy - dx
  xdata.append(x0); ydata.append(y0)

  y = y0

  for x in range(x0+xmod, x1+xmod, xmod):
    #print D
    if D > 0:
      y = y+ymod  # +1 or -1 dep on direction
      xdata.append(x); ydata.append(y)
      D += (2*dy - 2*dx)
    else:
      xdata.append(x); ydata.append(y)
      D += 2*dy

  return xdata,ydata


