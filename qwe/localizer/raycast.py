from numpy import clip, sin, cos, sign
from numpy.linalg import norm

def wall(x,y,theta,map):
  #print "wall: (%0.2f,%0.2f) @ %0.2f" % (x,y,theta)
  # note: maplen_xy will be one more than the hightest integer coord (eg 0-10 -> maplen=11)
  xpath,ypath = calc_line(x,y,theta,map.xdim,map.ydim)
  # TODO: move this check inside the line algorithm for speed
  for i in range(len(xpath)):
    if map.data[ypath[i]][xpath[i]] == 1:
      return xpath[i],ypath[i]
  return -1,-1  # no wall

# x_len, y_len are the lengths of the entire grid
def calc_line(x,y,theta,x_len,y_len):
  maxlen = norm([x_len,y_len])  # what about max sensor range?
  # find stright line coordinates far enough to be off the map
  xoff = int(x + maxlen * cos(theta))
  yoff = int(y + maxlen * sin(theta))
  #x = clip(x,0,mapx-1)
  #y = clip(y,0,mapy-1)
  return bresen(x,y,xoff,yoff, x_len-1,y_len-1)

def bresen(x0,y0, x1, y1, xmax, ymax):
  xdata = []
  ydata = []
 
  # TODO: use the subpixel value instead of ints
  x0 = int(x0)
  y0 = int(y0)
  #print "bresen: (%d,%d) - (%d,%d) max: (%d,%d)" % (x0, y0, x1, y1, xmax, ymax)

  dx = x1 - x0
  dy = y1 - y0
  xmod = sign(dx)
  ymod = sign(dy)
  dx = abs(dx)
  dy = abs(dy)

  # algorithm assumes dx >= dy, so swap if necessary
  if( dx < dy ):
    ydata,xdata = bresen(y0,x0,y1,x1,ymax,xmax)
    return xdata,ydata

  # TODO: preset this error term based on subpixel offset instead
  D = 2*dy - dx

  x = x0
  y = y0
  while (0 < x < xmax) and (0 < y < ymax): 
    x+=xmod
    if D > 0:
      y = y+ymod  # +1 or -1 dep on direction
      xdata.append(x); ydata.append(y)
      D += (2*dy - 2*dx)
    else:
      xdata.append(x); ydata.append(y)
      D += 2*dy

  return xdata,ydata


