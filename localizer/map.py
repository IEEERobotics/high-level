#!/usr/bin/python

from numpy import array
import csv

# loads map into 2d list:
#   [y][x] are map coordinates
#   [0][0] is bottom left corner
class Map():
  def __init__(self, filename):
    data = list( csv.reader(open(filename, 'r')))
    data = [ [int(x) for x in y] for y in data  ]  # convert string to ints
    data.reverse()
    self.data = data

  def xy(self):
    xy = []
    for y in range(len(self.data)):
      for x in range(len(self.data[0])):
        if self.data[y][x] == 1:
          xy.append([x,y])
    return array(xy)

  @property
  def xdim(self):
    return len(self.data[0])
  @property
  def ydim(self):
    return len(self.data)
  def __str__(self):
    return "Map: (%d, %d)" % (self.xdim, self.ydim)

