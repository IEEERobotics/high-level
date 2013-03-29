from numpy import array, clip, sin, cos, sign
from numpy.linalg import norm

def find_wall(x,y,theta,max_dist,map):

  x_end = x + max_dist * cos(theta)
  y_end = y + max_dist * sin(theta)

  x1 = int(x/map.scale)
  y1 = int(y/map.scale)
  x2 = int(x_end/map.scale)
  y2 = int(y_end/map.scale)

  wx,wy = raywall(x1,y1,x2,y2,map)
  #print "findwall: prescale: ", wx, wy
  wx *= map.scale
  wy *= map.scale

  return wx,wy


def raywall(x1, y1, x2, y2, map):
  """ raytrace until we hit a wall or end of our line """
  """ designed for integer grid coords, which represent starting/ending in the center of a space """
  # TODO: make this work with fractional offsets, which should just be preseeding error based on 
  #       our fractional part

  #print "raywall: (%d,%d)-(%d,%d)" % (x1,y1,x2,y2)

  dx = abs(x2 - x1)
  dy = abs(y2 - y1)
  x = x1
  y = y1
  n = 1 + dx + dy
  x_inc = sign(x2 - x1)
  y_inc = sign(y2 - y1)
  error = dx - dy
  dx *= 2
  dy *= 2

  xmax = map.xdim
  ymax = map.ydim
  while n > 0:
    if not (0<=x<xmax):
      return -1,-1
    if not (0<=y<ymax):
      return -1,-1
    if map.data[y][x] == 1:
      return x,y
    if error > 0:
      x += x_inc
      error -= dy
    else:
      y += y_inc
      error += dx
    n -= 1

  return -1,-1


################### old/experimental/broken ############################

def wall(x,y,theta,map,max_dist):
  """ x,y: sensor location in inches """
  print "wall: (%0.2f,%0.2f) @ %0.2f" % (x,y,theta)
  x /= map.scale
  y /= map.scale
  max_dist /= map.scale
  xpath,ypath = calc_line(x,y,theta,map.xdim-1,map.ydim-1, max_dist)  # dimension-1 since grid coords start at 0
  # TODO: move this check inside the line algorithm for speed
  for i in range(len(xpath)):
    if map.data[ypath[i]][xpath[i]] == 1:
      return xpath[i]*map.scale,ypath[i]*map.scale
  return -1,-1  # no wall

def calc_line(x,y,theta,grid_max_x,grid_max_y, max_dist):
  """ At this point, all x,y, and distances are in now normalized to grid size """
  """ Valid grid coordinates are (0..grid_max_x,0..grid_max_y) """
  print "calc_line: (%0.2f,%0.2f) @ %0.2f" % (x,y,theta)
  # find endpoints of line max_dist away
  x_end = x + max_dist * cos(theta)
  y_end = y + max_dist * sin(theta)
  print "calc_line: endpoints: ", x_end, y_end
 
  # calc some reasonable bounds for bresen alg
  # NB: this does NOT try to find a point on the line which is both 
  #     within the grid bounds and within max_dist, which might be better
  b_min_x = b_min_y = 0
  b_max_x = grid_max_x
  b_max_y = grid_max_y
  if( x < x_end < grid_max_x):
    b_max_x = x_end
  if( 0 < x_end < x):
    b_min_x = x_end
  if( y < y_end < grid_max_y):
    b_max_y = y_end
  if( 0 < y_end < y):
    b_min_y = y_end
  
  return b2(x,y,x_end,y_end, b_min_x,b_max_x,b_min_y,b_max_y)

def raytrace(x0, y0, x1, y1):
  """ calculates all squares intersected by a line """
  """ assumes integer grid coords, which represent starting/ending in the center of a space """
  # TODO: make this work with fractinal offsets, which should just be preseeding error based on 
  #       our fractional part

  dx = abs(x1 - x0)
  dy = abs(y1 - y0)
  x = x0
  y = y0
  n = 1 + dx + dy
  x_inc = sign(x1 - x0)
  y_inc = sign(y1 - y0)
  error = dx - dy
  dx *= 2
  dy *= 2

  xdata = [] 
  ydata = [] 

  while n > 0:
    xdata.append(x)
    ydata.append(y)
    if error > 0:
      x += x_inc
      error -= dy
    else:
      y += y_inc
      error += dx
    n -= 1

  return array([xdata,ydata])


def bresen(x1,y1, x2,y2, x_min,x_max, y_min,y_max):
  print "bresen: (%d,%d)->(%d,%d) bounds: (%0.2f,%0.2f),(%0.2f,%0.2f)" % (x1, y1, x2, y2, x_min, y_min, x_max,y_max)

  dx = x2 - x1
  dy = y2 - y1
  xmod = sign(dx)
  ymod = sign(dy)
  dx = abs(dx)
  dy = abs(dy)
  print "dx,dy: ", dx,dy

  # algorithm assumes dx >= dy, so swap if necessary
  if( dx < dy ):
    b = bresen(y1,x1,y2,x2,y_min,y_max,x_min,x_max)
    return array([b[1],b[0]])

  xdata = [x1]
  ydata = [y1]

  x_off = x1 - int(x1)
  y_off = x1 - int(y1)

  # TODO: preset this error term based on subpixel offset instead
  D = 2*dy - dx

  x = x1
  y = y1
  while (x_min < x < x_max) and (y_min < y < y_max): 
    x+=xmod
    if D > 0:
      y = y+ymod  # +1 or -1 dep on direction
      xdata.append(x); ydata.append(y)
      D += (2*dy - 2*dx)
    else:
      xdata.append(x); ydata.append(y)
      D += 2*dy

  return array([xdata,ydata])

def slope_walker(x1,y1, x2,y2):
  """ walk along the line using the slope
      relies on floating opint calculations
  """
  print "b2: (%d,%d)->(%d,%d) " % (x1, y1, x2, y2)

  dx = x2 - x1
  dy = y2 - y1
  xdir = sign(dx)
  ydir = sign(dy)
  dx = abs(dx)
  dy = abs(dy)
  print "dx,dy: ", dx,dy

  # algorithm assumes dx >= dy, so swap if necessary
  if( dx < dy ):
    b = b2(y1,x1,y2,x2,y_min,y_max,x_min,x_max)
    return array([b[1],b[0]])

  xdata = [x1]
  ydata = [y1]

  x = x1
  y = y1

  x_step = xdir 
  y_step = ydir * dy/dx

  x_diff = (x2 -x) * xdir
  y_diff = (y2- y)*ydir
  while (x_diff > 0) and (y_diff > 0): 
    x_int = int(x)
    y_int = int(y)
    #x_frac = x_int - x + 1
    #y_frac = y_int - y + 1
    #print "start fractionals: (%0.2f,%0.2f)" % (x_frac, y_frac)
    x += x_step
    y += y_step
    x_int2 = int(x)
    y_int2 = int(y)
    if (x_int != x_int2) and (y_int != y_int2):
      print "both changed"  
      # calculate overshoot (consider direction!)
      
    xdata.append(x)
    ydata.append(y)
    x_diff = (x2 -x) * xdir
    y_diff = (y2- y)*ydir
    

  return array([xdata,ydata])
