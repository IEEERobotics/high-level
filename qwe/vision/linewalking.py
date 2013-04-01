"""Navigation along a white line using visual feedback."""

import numpy as np

try:
  import cv2
except ImportError:
  print "You need OpenCV to use vision modules, sorry."
  sys.exit(1)

from util import Enum, rotateImage
from base import DependentFrameProcessor
from main import main
from linedetection import Line, LineDetector

class LineWalker(DependentFrameProcessor):
  """Navigates parallel to a white line boundary of a pickup/dropoff region."""
  
  State = Enum(['INIT', 'SEARCHING', 'GOOD', 'BAD', 'FAILED'])
  epsilonLineAngle = 2.0  # if white line is at an angle less than this, no correction is required (stops bot from oscillating around zero)
  maxLineAngle = 75.0  # if white line is at angle greater than this, either line detected is spurious or we are way off for line-walking
  
  def __init__(self, options, processorPool):
    DependentFrameProcessor.__init__(self, options, processorPool)
    self.detector = processorPool.getProcessorByType(LineDetector)
    if self.detector is None:
      self.loge("__init__", "Could not find a LineDetector; will not activate :(")
    self.state = LineWalker.State.INIT
  
  def initialize(self, imageIn, timeNow):
    #self.image = imageIn
    #self.imageSize = (self.image.shape[1], self.image.shape[0]) # (width, height)
    
    self.headingError = 0.0
    
    # [Sim] Need to get live values from bot_loc (?)
    self.sim = False
    self.heading = 0.0  # degrees
    
    if self.detector is not None:
      self.active = True
    else:
      self.state = LineWalker.State.FAILED
  
  def process(self, imageIn, timeNow):
    #self.image = imageIn
    
    self.headingError = 0.0
    
    # [Sim] Turn imageIn by current angle = self.heading
    if self.sim and self.heading != 0.0:
      #self.logd("process", "Heading = %.2f" % self.heading)
      imageIn = rotateImage(imageIn, self.heading)
    
    # Grab detected line, if any
    if self.detector is None:
      return  # skip if we don't have a detector and were still called to process
    self.state = LineWalker.State.SEARCHING
    if self.detector.state is LineDetector.State.FOUND:  # skip if line not found
      # TODO skip if confidence is low
      whiteLine = self.detector.primaryLine
      if self.gui:
        cv2.circle(self.detector.imageOut, whiteLine.ptLeft, 10, (255, 0, 0), 2)
        cv2.circle(self.detector.imageOut, whiteLine.ptRight, 10, (255, 0, 0), 2)
      
      if whiteLine.valid and abs(whiteLine.angle) >= self.epsilonLineAngle and abs(whiteLine.angle) <= self.maxLineAngle:
        # Compute heading error between self and line; TODO use actual bot heading, and reject very high changes (position, angle) as invalid
        self.headingError = -whiteLine.angle
        self.state = LineWalker.State.GOOD
      else:
        self.state = LineWalker.State.BAD
        
        # [Sim] Artificially change self heading
        if self.sim and self.headingError != 0.0:
          if whiteLine.ptLeft[1] < whiteLine.ptRight[1]:
            self.heading += 1.0
          else:
            self.heading -= 1.0
      
    # TODO Based on self.detector.state, iterate through move-check loop
    
    return True, self.detector.imageOut
  
  def onKeyPress(self, key, keyChar=None):
    if keyChar == None:  # special key
      keyByte = key & 0xff
      
      if keyByte == 0x51:  # LEFT
        self.heading -= 1.0
      elif keyByte == 0x53:  # RIGHT
        self.heading += 1.0
    
    return True
