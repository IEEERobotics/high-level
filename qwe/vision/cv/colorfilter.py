"""
Image filter used to extract blobs based on color.
Filter bank:-
blue: [105 100 100] - [115 255 255]
brown: [170  50  50] - [ 20 200 140]
yellow: [ 18 150 150] - [ 32 255 255]
red: [175 100 100] - [ 15 255 255]
"""

import numpy as np
import cv2
import cv2.cv as cv
from base import FrameProcessor
from main import main

class FilterHSV:
  """Represents a simple HSV color filter."""
  minHSV = np.array([0, 0, 0], np.uint8)  # minimum possible values of HSV
  maxHSV = np.array([180, 255, 255], np.uint8)  # maximum possible values of HSV
  
  def __init__(self):
    self.lower = self.minHSV  # lower bound
    self.upper = self.maxHSV  # upper bound
  
  def apply(self, imageHSV):
    """Apply this filter to a given image."""
    # Handle hue wrap-around
    maskH = None
    if self.lower[0] > self.upper[0]:
      maskH_high = cv2.inRange(imageHSV[:,:,0], np.asarray(self.lower[0]), np.asarray(FilterHSV.maxHSV[0]))
      maskH_low  = cv2.inRange(imageHSV[:,:,0], np.asarray(FilterHSV.minHSV[0]), np.asarray(self.upper[0]))
      maskH = maskH_high | maskH_low
    else:
      maskH = cv2.inRange(imageHSV[:,:,0], np.asarray(self.lower[0]), np.asarray(self.upper[0]))
    
    maskS = cv2.inRange(imageHSV[:,:,1], np.asarray(self.lower[1]), np.asarray(self.upper[1]))
    maskV = cv2.inRange(imageHSV[:,:,2], np.asarray(self.lower[2]), np.asarray(self.upper[2]))
    return maskH & maskS & maskV
    #return cv2.inRange(imageHSV, self.lower, self.upper)  # direct application without hue wrap-around
  
  def __str__(self):
    return str(self.lower) + " - " + str(self.upper)
  
  def toXMLString(self):
    """Return an XML representation of the current state of this filter."""
    return ("<FilterHSV>"
           "<lower><H>%d</H><S>%d</S><V>%d</V></lower>"
           "<upper><H>%d</H><S>%d</S><V>%d</V></upper>"
           "</FilterHSV>") % (self.lower[0], self.lower[1], self.lower[2],
                              self.upper[0], self.upper[1], self.upper[2])
  
  def copy(self):
    """Return a deep copy of this filter."""
    clone = FilterHSV()
    clone.lower = self.lower.copy()
    clone.upper = self.upper.copy()
    return clone
  
class ColorFilter(FrameProcessor):
  """Detects different colored blobs and identifies their color."""
  channelsHSV = "HSV"  # HSV channel names for display = array('c', "HSV")
  
  def __init__(self):
    FrameProcessor.__init__(self)
    self.debug = True
  
  def initialize(self, imageIn, timeNow):
    self.image = imageIn
    self.imageSize = (self.image.shape[1], self.image.shape[0])  # (width, height)
    
    self.filterBank = { }
    self.filterHSV = FilterHSV()
    self.filterHSV.lower = np.array([105, 100, 100], np.uint8)
    self.filterHSV.upper = np.array([115, 255, 255], np.uint8)
    self.logd("initialize", "HSV filter: " + str(self.filterHSV.lower) + " - " + str(self.filterHSV.upper))
    
    self.lowerPatch = np.array([[self.filterHSV.lower]])  
    self.upperPatch = np.array([[self.filterHSV.upper]])  # 1x1 pixel image (array) for HSV upper-bound display
    
    self.channel = 0
    
    self.hueSpan = (self.filterHSV.upper[0] - self.filterHSV.lower[0]) % FilterHSV.maxHSV[0]
    self.hue = (self.filterHSV.lower[0] + self.hueSpan / 2) % FilterHSV.maxHSV[0]
    
    self.winName = "Color Filter"
    cv2.namedWindow(self.winName)
    cv2.createTrackbar("Hue", self.winName, self.hue, FilterHSV.maxHSV[0], self.onTrackbarChange)
    cv2.createTrackbar("Hue span", self.winName, self.hueSpan, FilterHSV.maxHSV[0], self.onTrackbarChange)
    cv2.createTrackbar("Sat min", self.winName, self.filterHSV.lower[1], FilterHSV.maxHSV[1], self.onTrackbarChange)
    cv2.createTrackbar("Sat max", self.winName, self.filterHSV.upper[1], FilterHSV.maxHSV[1], self.onTrackbarChange)
    cv2.createTrackbar("Val min", self.winName, self.filterHSV.lower[2], FilterHSV.maxHSV[2], self.onTrackbarChange)
    cv2.createTrackbar("Val max", self.winName, self.filterHSV.upper[2], FilterHSV.maxHSV[2], self.onTrackbarChange)
  
  def process(self, imageIn, timeNow):
    self.image = imageIn

    self.imageHSV = cv2.cvtColor(self.image, cv.CV_BGR2HSV)
    #cv2.imshow("HSV", self.imageHSV)
    #cv2.imshow("H", self.imageHSV[:,:,0])
    #cv2.imshow("S", self.imageHSV[:,:,1])
    #cv2.imshow("V", self.imageHSV[:,:,2])
    
    self.maskHSV = self.filterHSV.apply(self.imageHSV)
    self.imageMasked = cv2.bitwise_and(self.image, np.array([255, 255, 255], np.uint8), mask=self.maskHSV)
    
    lowerPatch = np.array([[self.filterHSV.lower]])  # 1x1 image for lower-bound display
    upperPatch = np.array([[self.filterHSV.upper]])  # 1x1 image for upper-bound display
    self.imageMasked[10:50, 10:50, :] = cv2.cvtColor(lowerPatch, cv.CV_HSV2BGR)
    self.imageMasked[10:50, 51:90, :] = cv2.cvtColor(upperPatch, cv.CV_HSV2BGR)
    cv2.imshow(self.winName, self.imageMasked)
    
    return True, self.maskHSV
  
  def onKeyPress(self, key, keyChar=None):
    # Change current channel to H, S or V, or channel values
    if keyChar == 'h' or keyChar == 'H':
      self.channel = 0
    elif keyChar == 's' or keyChar == 'S':
      self.channel = 1
    elif keyChar == 'v' or keyChar == 'V':
      self.channel = 2
    elif keyChar == ',':  # decrement lower bound
      self.filterHSV.lower[self.channel] = self.filterHSV.lower[self.channel] - 1 if self.filterHSV.lower[self.channel] > FilterHSV.minHSV[self.channel] else self.filterHSV.lower[self.channel]
    elif keyChar == '.':  # increment lower bound
      self.filterHSV.lower[self.channel] = self.filterHSV.lower[self.channel] + 1 if self.filterHSV.lower[self.channel] < self.filterHSV.upper[self.channel] else self.filterHSV.lower[self.channel]
    elif keyChar == '<':  # decrement upper bound
      self.filterHSV.upper[self.channel] = self.filterHSV.upper[self.channel] - 1 if self.filterHSV.upper[self.channel] > self.filterHSV.lower[self.channel] else self.filterHSV.upper[self.channel]
    elif keyChar == '>':  # increment upper bound
      self.filterHSV.upper[self.channel] = self.filterHSV.upper[self.channel] + 1 if self.filterHSV.upper[self.channel] < FilterHSV.maxHSV[self.channel] else self.filterHSV.upper[self.channel]
    elif keyChar == 'x':
      print self.filterHSV.toXMLString()
      return True
    elif keyChar == 'a':
      filterName = raw_input("Add HSV filter to bank with name: ")
      if len(filterName) > 0:
        self.filterBank[filterName] = self.filterHSV.copy()
      return True
    elif keyChar == 'l':
      print "%d filters in bank" % len(self.filterBank)
      for filterName, filterHSV in self.filterBank.iteritems():
        print filterName + ": " + str(filterHSV)
      print
      return True
    else:
      return True
    
    # If channel or channel values were changed, display current state, and optionally update trackbars
    self.logd("onKeyPress", "Channel: " + self.channelsHSV[self.channel] + ", HSV filter: " + str(self.filterHSV))
    #self.updateTrackbars()  # TODO Fix hue trackbar issue and re-enable
    return True
  
  def onTrackbarChange(self, value):
    self.hue = cv2.getTrackbarPos("Hue", self.winName)
    self.hueSpan = cv2.getTrackbarPos("Hue span", self.winName)
    self.filterHSV.lower[0] = (self.hue - self.hueSpan / 2) % FilterHSV.maxHSV[0]
    self.filterHSV.upper[0] = (self.hue + self.hueSpan / 2) % FilterHSV.maxHSV[0]
    self.filterHSV.lower[1] = cv2.getTrackbarPos("Sat min", self.winName)
    self.filterHSV.upper[1] = cv2.getTrackbarPos("Sat max", self.winName)
    self.filterHSV.lower[2] = cv2.getTrackbarPos("Val min", self.winName)
    self.filterHSV.upper[2] = cv2.getTrackbarPos("Val max", self.winName)
    #self.logd("onTrackbarChange", ", HSV filter: " + self.filterHSV)
  
  def updateTrackbars(self):
    # TODO Resolve issue: setTrackbarPos() in turn fires trackbar change events and hue, hueSpan get computed twice and become degenrate
    self.hueSpan = self.filterHSV.upper[0] - self.filterHSV.lower[0]
    self.hue = (self.filterHSV.lower[0] + self.filterHSV.upper[0]) / 2
    #self.hueSpan = (self.filterHSV.upper[0] - self.filterHSV.lower[0]) if self.filterHSV.lower[0] <= self.filterHSV.upper[0] else FilterHSV.maxHSV[0] - (self.filterHSV.lower[0] - self.filterHSV.upper[0])
    #self.hue = (self.filterHSV.lower[0] + int((self.hueSpan / 2) + 0.5)) % FilterHSV.maxHSV[0]
    cv2.setTrackbarPos("Hue", self.winName, self.hue)
    cv2.setTrackbarPos("Hue span", self.winName, self.hueSpan)
    cv2.setTrackbarPos("Sat min", self.winName, self.filterHSV.lower[1])
    cv2.setTrackbarPos("Sat max", self.winName, self.filterHSV.upper[1])
    cv2.setTrackbarPos("Val min", self.winName, self.filterHSV.lower[2])
    cv2.setTrackbarPos("Val max", self.winName, self.filterHSV.upper[2])


# Run a ColorFilter instance using main.main()
if __name__ == "__main__":
  main(ColorFilter)
