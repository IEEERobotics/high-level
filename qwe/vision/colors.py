"""Defines different colors and comparison methods."""

import sys
from math import sqrt

class Color:
  def __init__(self, name, rgb, cmyk):
    self.name = name
    self.rgb = rgb
    self.cmyk = cmyk
  
  def compareWithRGB(self, rgb):
    return sqrt((self.rgb[0] - rgb[0])^2 + (self.rgb[1] - rgb[1])^2 + (self.rgb[2] - rgb[2])^2)
  
  def compareWithBGR(self, bgr):
    return sqrt(float(self.rgb[0] - bgr[2])**2 + float(self.rgb[1] - bgr[1])**2 + float(self.rgb[2] - bgr[0])**2)
  
  def __str__(self):
    return "<Color {name} {rgb} {cmyk}>".format(name=self.name, rgb=self.rgb, cmyk=self.cmyk)

# Color set 01: Based on paint colors as per specs
colorSet01 = dict(
  green = Color("green", (0, 73, 36), (89, 42, 98, 48)),  # Hunter Green
  red = Color("red", (146, 1, 32), (26, 100, 92, 27)),  # Colonial Red
  brown = Color("brown", (63, 9, 11), (48, 83, 73, 73)),  # Kona Brown
  yellow = Color("yellow", (250, 234, 51), (5, 1, 90, 0)),  # Sun Yellow
  blue = Color("blue", (0, 117, 187), (87, 50, 1, 0)),  # Brilliant Blue
  orange = Color("orange", (229, 97, 23), (5, 76, 100, 1)),  # Real Orange
  white = Color("white", (242, 235, 207), (5, 5, 20, 0)),  # Heirloom White
  )

# Pick default set
colors = colorSet01

def findMatchColorBGR(colors, bgr, max_diff=sys.float_info.max):
  """Given a color as BGR, find its closest matching Color object from colors dict."""
  minDiff = max_diff
  matchColor = None
  for name, color in colors.iteritems():
    diff = color.compareWithBGR(bgr)
    if diff < minDiff:
      minDiff = diff
      matchColor = color
  return matchColor

def testMatchColorBGR(bgr):
  matchColor = findMatchColorBGR(colors, bgr)
  if matchColor is not None:
    print "testMatchColor(): {0} is {1} (rgb={2})".format(bgr, matchColor.name, matchColor.rgb)
  else:
    print "testMatchColor(): No matching color found for {0}".format(bgr)

if __name__ == "__main__":
  print "__main__: {0} colors:".format(len(colors))
  for name, color in colors.iteritems():
    print "{name}: {color}".format(name=name, color=color)
  
  testMatchColorBGR((10, 90, 25))
  testMatchColorBGR((150, 12, 96))
  testMatchColorBGR((122, 97, 20))
