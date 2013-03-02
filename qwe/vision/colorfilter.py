"""
Image filter used to extract blobs based on color.
Filter bank:-
blue: [105 100 100] - [115 255 255]
brown: [170  50  50] - [ 20 200 140]
yellow: [ 18 150 150] - [ 32 255 255]
red: [175 100 100] - [ 15 255 255]
"""

import pickle
import json
import numpy as np
import cv2
import cv2.cv as cv
from base import FrameProcessor
from main import main

class HSVFilter:
  """Represents a simple HSV color filter."""
  minHSV = np.array([0, 0, 0], np.uint8)  # minimum possible values of HSV
  maxHSV = np.array([180, 255, 255], np.uint8)  # maximum possible values of HSV
  
  def __init__(self, lower=minHSV, upper=maxHSV):
    self.lower = lower  # lower bound
    self.upper = upper  # upper bound
  
  def apply(self, imageHSV):
    """Apply this filter to a given image."""
    # Handle hue wrap-around
    maskH = None
    if self.lower[0] > self.upper[0]:
      maskH_high = cv2.inRange(imageHSV[:,:,0], np.asarray(self.lower[0]), np.asarray(HSVFilter.maxHSV[0]))
      maskH_low  = cv2.inRange(imageHSV[:,:,0], np.asarray(HSVFilter.minHSV[0]), np.asarray(self.upper[0]))
      maskH = maskH_high | maskH_low
    else:
      maskH = cv2.inRange(imageHSV[:,:,0], np.asarray(self.lower[0]), np.asarray(self.upper[0]))
    
    maskS = cv2.inRange(imageHSV[:,:,1], np.asarray(self.lower[1]), np.asarray(self.upper[1]))
    maskV = cv2.inRange(imageHSV[:,:,2], np.asarray(self.lower[2]), np.asarray(self.upper[2]))
    return maskH & maskS & maskV
    #return cv2.inRange(imageHSV, self.lower, self.upper)  # direct application without hue wrap-around
  
  def __str__(self):
    return str(self.lower) + " - " + str(self.upper)
  
  def toString(self):
    return self.__class__.__name__ + "\t" + "\t".join(str(x) for x in self.lower) + "\t" + "\t".join(str(x) for x in self.upper)
  
  def toJSONString(self):
    return "{ \"__class__\": \"" + self.__class__.__name__ + "\", \"lower\": " + json.dumps(self.lower.tolist()) + ", \"upper\": " + json.dumps(self.upper.tolist()) + " }"
    #return "{ \"__class__\": \"" + self.__class__.__name__ + "\", \"lower\": [" + ", ".join(str(x) for x in self.lower) + "], \"upper\": [" + ", ".join(str(x) for x in self.upper) + "] }"
  
  def toXMLString(self):
    """Return an XML representation of the current state of this filter."""
    return ("<HSVFilter>"
           "<lower><H>%d</H><S>%d</S><V>%d</V></lower>"
           "<upper><H>%d</H><S>%d</S><V>%d</V></upper>"
           "</HSVFilter>") % (self.lower[0], self.lower[1], self.lower[2],
                              self.upper[0], self.upper[1], self.upper[2])
  
  def copy(self):
    """Return a deep copy of this filter."""
    clone = HSVFilter(lower=self.lower.copy(), upper=self.upper.copy())
    return clone
  
class ColorFilterProcessor(FrameProcessor):
  """Detects different colored areas using filters."""
  channelsHSV = "HSV"  # HSV channel names for display = array('c', "HSV")
  
  def __init__(self):
    FrameProcessor.__init__(self)
    self.debug = True
  
  def initialize(self, imageIn, timeNow):
    self.image = imageIn
    self.imageSize = (self.image.shape[1], self.image.shape[0])  # (width, height)
    
    self.filterBank = { }
    self.colorFilter = HSVFilter()
    self.colorFilter.lower = np.array([105, 100, 100], np.uint8)
    self.colorFilter.upper = np.array([115, 255, 255], np.uint8)
    self.logd("initialize", "HSV filter: " + str(self.colorFilter.lower) + " - " + str(self.colorFilter.upper))
    print "*** Menu ***"
    print "\ta\tAdd current filter to bank"
    print "\tl\tList filters in bank"
    print "\tw\tWrite bank to file (as JSON)"
    print "\tr\tRead bank from file (replaces current bank)"
    print
    
    self.lowerPatch = np.array([[self.colorFilter.lower]])  
    self.upperPatch = np.array([[self.colorFilter.upper]])  # 1x1 pixel image (array) for HSV upper-bound display
    
    self.channel = 0
    
    self.hueSpan = (self.colorFilter.upper[0] - self.colorFilter.lower[0]) % HSVFilter.maxHSV[0]
    self.hue = (self.colorFilter.lower[0] + self.hueSpan / 2) % HSVFilter.maxHSV[0]
    
    self.winName = "Color Filter"
    cv2.namedWindow(self.winName)
    cv2.createTrackbar("Hue", self.winName, self.hue, HSVFilter.maxHSV[0], self.onTrackbarChange)
    cv2.createTrackbar("Hue span", self.winName, self.hueSpan, HSVFilter.maxHSV[0], self.onTrackbarChange)
    cv2.createTrackbar("Sat min", self.winName, self.colorFilter.lower[1], HSVFilter.maxHSV[1], self.onTrackbarChange)
    cv2.createTrackbar("Sat max", self.winName, self.colorFilter.upper[1], HSVFilter.maxHSV[1], self.onTrackbarChange)
    cv2.createTrackbar("Val min", self.winName, self.colorFilter.lower[2], HSVFilter.maxHSV[2], self.onTrackbarChange)
    cv2.createTrackbar("Val max", self.winName, self.colorFilter.upper[2], HSVFilter.maxHSV[2], self.onTrackbarChange)
  
  def process(self, imageIn, timeNow):
    self.image = imageIn

    self.imageHSV = cv2.cvtColor(self.image, cv.CV_BGR2HSV)
    #cv2.imshow("HSV", self.imageHSV)
    #cv2.imshow("H", self.imageHSV[:,:,0])
    #cv2.imshow("S", self.imageHSV[:,:,1])
    #cv2.imshow("V", self.imageHSV[:,:,2])
    
    self.maskHSV = self.colorFilter.apply(self.imageHSV)
    self.imageMasked = cv2.bitwise_and(self.image, np.array([255, 255, 255], np.uint8), mask=self.maskHSV)
    
    lowerPatch = np.array([[self.colorFilter.lower]])  # 1x1 image for lower-bound display
    upperPatch = np.array([[self.colorFilter.upper]])  # 1x1 image for upper-bound display
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
      self.colorFilter.lower[self.channel] = self.colorFilter.lower[self.channel] - 1 if self.colorFilter.lower[self.channel] > HSVFilter.minHSV[self.channel] else self.colorFilter.lower[self.channel]
    elif keyChar == '.':  # increment lower bound
      self.colorFilter.lower[self.channel] = self.colorFilter.lower[self.channel] + 1 if self.colorFilter.lower[self.channel] < self.colorFilter.upper[self.channel] else self.colorFilter.lower[self.channel]
    elif keyChar == '<':  # decrement upper bound
      self.colorFilter.upper[self.channel] = self.colorFilter.upper[self.channel] - 1 if self.colorFilter.upper[self.channel] > self.colorFilter.lower[self.channel] else self.colorFilter.upper[self.channel]
    elif keyChar == '>':  # increment upper bound
      self.colorFilter.upper[self.channel] = self.colorFilter.upper[self.channel] + 1 if self.colorFilter.upper[self.channel] < HSVFilter.maxHSV[self.channel] else self.colorFilter.upper[self.channel]
    elif keyChar == 'x':
      print self.colorFilter.toXMLString()
      return True
    elif keyChar == 'a':
      filterName = raw_input("Add HSV filter to bank with name: ")
      if len(filterName) > 0:
        self.filterBank[filterName] = self.colorFilter.copy()
      return True
    elif keyChar == 'l':
      self.printFilterBank()
      return True
    elif keyChar == 'w':
      outFilename = raw_input("Write filter bank to file: ")
      self.writeFilterBankJSON(outFilename)
      return True
    elif keyChar == 'r':
      inFilename = raw_input("Read filter bank from file: ")
      self.readFilterBankJSON(inFilename)
      return True
    else:
      return True
    
    # If channel or channel values were changed, display current state, and optionally update trackbars
    self.logd("onKeyPress", "Channel: " + self.channelsHSV[self.channel] + ", HSV filter: " + str(self.colorFilter))
    #self.updateTrackbars()  # TODO Fix hue trackbar issue and re-enable
    return True
  
  def onTrackbarChange(self, value):
    self.hue = cv2.getTrackbarPos("Hue", self.winName)
    self.hueSpan = cv2.getTrackbarPos("Hue span", self.winName)
    self.colorFilter.lower[0] = (self.hue - self.hueSpan / 2) % HSVFilter.maxHSV[0]
    self.colorFilter.upper[0] = (self.hue + self.hueSpan / 2) % HSVFilter.maxHSV[0]
    self.colorFilter.lower[1] = cv2.getTrackbarPos("Sat min", self.winName)
    self.colorFilter.upper[1] = cv2.getTrackbarPos("Sat max", self.winName)
    self.colorFilter.lower[2] = cv2.getTrackbarPos("Val min", self.winName)
    self.colorFilter.upper[2] = cv2.getTrackbarPos("Val max", self.winName)
    #self.logd("onTrackbarChange", ", HSV filter: " + self.colorFilter)
  
  def updateTrackbars(self):
    # TODO Resolve issue: setTrackbarPos() in turn fires trackbar change events and hue, hueSpan get computed twice and become degenrate
    self.hueSpan = self.colorFilter.upper[0] - self.colorFilter.lower[0]
    self.hue = (self.colorFilter.lower[0] + self.colorFilter.upper[0]) / 2
    #self.hueSpan = (self.colorFilter.upper[0] - self.colorFilter.lower[0]) if self.colorFilter.lower[0] <= self.colorFilter.upper[0] else HSVFilter.maxHSV[0] - (self.colorFilter.lower[0] - self.colorFilter.upper[0])
    #self.hue = (self.colorFilter.lower[0] + int((self.hueSpan / 2) + 0.5)) % HSVFilter.maxHSV[0]
    cv2.setTrackbarPos("Hue", self.winName, self.hue)
    cv2.setTrackbarPos("Hue span", self.winName, self.hueSpan)
    cv2.setTrackbarPos("Sat min", self.winName, self.colorFilter.lower[1])
    cv2.setTrackbarPos("Sat max", self.winName, self.colorFilter.upper[1])
    cv2.setTrackbarPos("Val min", self.winName, self.colorFilter.lower[2])
    cv2.setTrackbarPos("Val max", self.winName, self.colorFilter.upper[2])
  
  def getFilterBankJSON(self):
    filterJSONs = [ ]  # list of JSON strings, one for each filter in bank
    for filterName, colorFilter in self.filterBank.iteritems():
      filterJSONs.append("\"" + filterName + "\": " + colorFilter.toJSONString())
    print
    return "{ " + ", ".join(filterJSONs) + " }"
  
  def printFilterBank(self, filterBank=None):
    if filterBank is None:
      filterBank = self.filterBank
    print "%d filter(s) in bank" % len(filterBank)
    for filterName, colorFilter in filterBank.iteritems():
      print filterName + ": " + str(colorFilter)
  
  def writeFilterBankJSON(self, outFilename):
    """Write filter bank to file (JSON)."""
    filterBankJSON = self.getFilterBankJSON()  # encode filter bank to JSON string
    print "Filter bank JSON: " + filterBankJSON
    
    filterBankDict = json.loads(filterBankJSON)  # decode JSON to validate format
    filterBankJSONfinal = json.dumps(filterBankDict, indent=2)  # re-encode with indentation
    print "Filter bank JSON (final):\n" + filterBankJSONfinal
    
    #print "Current filter JSON: " + self.colorFilter.toJSONString()
    #print "Pickled filter bank: " + pickle.dumps(self.filterBank)
    
    try:
      outFile = open(outFilename, 'w')
      outFile.write(filterBankJSONfinal)
      outFile.close()
    except IOError:
      print "I/O error; couldn't write to file: " + outFilename
    else:
      print "Done."
  
  def readFilterBankJSON(self, inFilename):
    """Read filter bank from file (JSON)."""
    try:
      inFile = open(inFilename, 'r')
      filterBankJSON = inFile.read()
      inFile.close()
    except IOError:
      print "I/O error; couldn't read from file: " + inFilename
    else:
      print "Filter bank JSON: " + filterBankJSON
      # TODO Parse JSON string and fill in filter bank
      filterBank = { }
      filterBankDict = json.loads(filterBankJSON)
      for filterName, filterDict in filterBankDict.iteritems():
        colorFilter = HSVFilter(lower=np.array(filterDict["lower"], dtype=np.uint8), upper=np.array(filterDict["upper"], dtype=np.uint8))
        filterBank[filterName] = colorFilter
      
      self.filterBank = filterBank
      print "Done."
      self.printFilterBank()


# Run a ColorFilterProcessor instance using main.main()
if __name__ == "__main__":
  main(ColorFilterProcessor)
