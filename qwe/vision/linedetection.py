"""White line detection."""
# For usage, see pycv.main module.

from math import sqrt, atan2, degrees
import numpy as np
import cv2
from util import Enum
from base import DependentFrameProcessor
from main import main
from colorfilter import ColorFilterProcessor

class Line:
  """Represents a line in 2D space."""
  
  def __init__(self, pt1, pt2, imageSize=None):
    if pt1[0] <= pt2[0]:  # ensure pt1 is to the left of pt2 for easier computations later on
      self.pt1 = pt1
      self.pt2 = pt2
    else:
      self.pt1 = pt2
      self.pt2 = pt1
    self.delta = np.subtract(self.pt2, self.pt1)
    self.length = sqrt(self.delta[0]**2 + self.delta[1]**2)
    self.m = float(self.delta[1]) / float(self.delta[0]) if self.delta[0] != 0.0 else (np.inf if self.delta[1] >=0 else -np.inf)
    self.c = self.pt1[1] - self.m * self.pt1[0]
    #print "delta = {0}, m = {1}, c = {2}".format(self.delta, self.m, self.c)
    
    # Check for validity/stability
    if np.isinf(self.m) or np.isinf(self.c):
      self.angle = 0.0
      self.valid = False
      return
    
    # Compute angle in degrees
    self.angle = degrees(atan2(self.delta[1], self.delta[0]))
    self.valid = True
    
    # Compute points on left and right edges, if an imageSize is given
    if imageSize is None:
      self.ptLeft = self.pt1
      self.ptRight = self.pt2
    else:
      self.ptLeft = (0, int(self.c))
      self.ptRight = (imageSize[0] - 1, int(self.m * (imageSize[0] - 1) + self.c))
  
  def renderTo(self, imageOut):
    if np.isinf(self.m) or np.isinf(self.c):
      return
    
    #dispPt1 = (0, int(self.c))
    #dispPt2 = (imageOut.shape[1], int(self.m * imageOut.shape[1] + self.c))
    
    # TODO Clip points to imageOut, or rely on clipping in cv2.line()?  
    cv2.line(imageOut, self.ptLeft, self.ptRight, (0, 255, 0), 2)
    
    cv2.circle(imageOut, self.pt1, 25, (0, 255, 255), 2)
    cv2.circle(imageOut, self.pt2, 25, (255, 255, 0), 2)


class LineDetector(DependentFrameProcessor):
  """Detects thick white lines."""

  State = Enum(['INIT', 'SEARCHING', 'FOUND', 'FAILED'])
  maxCornerMatchDiff = 0.75
  minGoodFrames = 5
  maxBadFrames = 15
  
  def __init__(self, options, processorPool):
    DependentFrameProcessor.__init__(self, options, processorPool)
    self.colorFilterProcessor = processorPool.getProcessorByType(ColorFilterProcessor)
    if self.colorFilterProcessor is None:
      self.loge("__init__", "Could not find a ColorFilterProcessor; will use internal white filter")
    #self.debug = True  # override debug flag
    self.state = LineDetector.State.INIT
  
  def initialize(self, imageIn, timeNow):
    self.image = imageIn
    self.imageSize = (self.image.shape[1], self.image.shape[0]) # (width, height)
    self.imageOut = self.image.copy() if self.gui else None
    self.goodFrames = 0
    self.badFrames = 0
    self.logd("initialize", "Image size = " + str(self.imageSize))
    
    # Define corner template
    self.templateCorner = np.zeros((60, 60), np.uint8)
    self.templateCornerOffset = np.divide(self.templateCorner.shape, 2)
    cv2.rectangle(self.templateCorner, (0, 0), (40, 40), 255, cv2.cv.CV_FILLED)
    cv2.rectangle(self.templateCorner, (0, 0), (20, 20), 0, cv2.cv.CV_FILLED)
    if self.gui: cv2.imshow("Corner template", self.templateCorner)
    self.minLineLength = sqrt(self.templateCorner.shape[0]**2 + self.templateCorner.shape[1]**2)  # the two line end points found must be at least this much apart to be a valid line
    
    # TODO Define T template
    
    self.state = LineDetector.State.SEARCHING
    self.active = True
  
  def process(self, imageIn, timeNow):
    self.image = imageIn
    if self.gui: self.imageOut = self.image.copy()
    
    # * Try to get white mask from a ColorFilterProcessor, if available
    maskWhite = None
    if self.colorFilterProcessor is not None and self.colorFilterProcessor.active and self.colorFilterProcessor.state == ColorFilterProcessor.State.LIVE:
      maskWhite = self.colorFilterProcessor.masks['white']
    
    # * If we don't have a ColorFilterProcessor or if it couldn't give us a white mask, compute it
    if maskWhite is None:
      # * Obtain grayscale image
      #gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
      #if self.gui: cv2.imshow("Gray", gray)
      
      # * Convert image to HSV space, and extract H, S, V channels
      imageHSV = cv2.cvtColor(self.image, cv2.COLOR_BGR2HSV_FULL)
      imageH, imageS, imageV = cv2.split(imageHSV)
      #if self.gui:
      #  cv2.imshow("Hue", imageH)
      #  cv2.imshow("Sat", imageS)
      #  cv2.imshow("Val", imageV)
      
      # * Apply saturation-value filter to extract white regions
      _, maskLowSat = cv2.threshold(imageS, 64, 255, cv2.THRESH_BINARY_INV)
      _, maskHighVal = cv2.threshold(imageV, 192, 255, cv2.THRESH_BINARY)
      #if self.gui:
      #  cv2.imshow("Low sat mask", maskLowSat)
      #  cv2.imshow("High val mask", maskHighVal)
      maskWhite = cv2.bitwise_and(maskLowSat, maskHighVal)
    
    # * Improve white mask by applying morphological filter
    maskWhite = cv2.morphologyEx(maskWhite, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    if self.gui: cv2.imshow("White mask", maskWhite)
    
    # * Convolve corner template over white mask to find corners
    methodMatchCorner = cv2.cv.CV_TM_SQDIFF_NORMED
    matchCorner = cv2.matchTemplate(maskWhite, self.templateCorner, methodMatchCorner)
    if self.gui and self.debug: cv2.imshow("Corner match", matchCorner)
    
    # * Find first corner as the point with best response
    self.state = LineDetector.State.SEARCHING
    minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(matchCorner)
    #self.logd("process", "minVal = {0}, maxVal = {1}, minLoc = {2}, maxLoc = {3}".format(minVal, maxVal, minLoc, maxLoc))
    if minVal <= self.maxCornerMatchDiff:  # only for methodMatchCorner == cv2.cv.CV_TM_SQDIFF_NORMED; TODO other methods will need an inverse bound
      bestLoc = minLoc if methodMatchCorner == cv2.cv.CV_TM_SQDIFF_NORMED else maxLoc
      bestLocCorrected = tuple(np.add(bestLoc, self.templateCornerOffset))
      linePt1 = bestLocCorrected
      
      # ** Occlude first corner region to find next corner point
      cv2.circle(matchCorner, bestLoc, 25, 1.0, cv2.cv.CV_FILLED)
      minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(matchCorner)
      bestLoc = minLoc if methodMatchCorner == cv2.cv.CV_TM_SQDIFF_NORMED else maxLoc
      bestLocCorrected = tuple(np.add(bestLoc, self.templateCornerOffset))
      linePt2 = bestLocCorrected
      
      # TODO Use a better method (like line fitting through local minima) to compute line
      # TODO Use fit error as an uncertainty measure
      
      # ** Find a line passing through corners found
      self.primaryLine = Line(linePt1, linePt2, self.imageSize)
      
      # ** TODO Convolve T template to find T junctions, and line passing through them
      # ** TODO Test which is more robust (corners vs T junctions) and pick one method
      
      # ** Set state to FOUND if a valid line was found in this frame
      if self.primaryLine.length >= self.minLineLength:
        self.state = LineDetector.State.FOUND
        if self.gui: self.primaryLine.renderTo(self.imageOut)
      
      # TODO Set state based on whether a consistent line was found or not (goodFrames >= minGoodFrames)
    
    # TODO If too many frames have passed (badFrames > maxBadFrames), signal failure (set state to FAILED)
    
    #self.logd("process", "[{0}]".format(LineDetector.State.toString(self.state)));
    return True, self.imageOut


# Run a LineDetector instance using pycv.main.main()
if __name__ == "__main__":
  main(LineDetector)
