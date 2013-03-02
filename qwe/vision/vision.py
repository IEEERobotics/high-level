"""
Vision module to manage different processors.
"""

import numpy as np
import cv2
from util import KeyCode, log
from base import FrameProcessor
from colorfilter import ColorFilterProcessor

class VisionManager:
  def __init__(self, context):
    self.context = context
    self.debug = True
  
  def start(self):
    # Parameters and flags
    delay = 20
    showInput = True
    showOutput = True
    showFPS = False
    
    # * Try to open camera
    self.logd("start", "Opening camera...")
    isOkay = False
    camera = cv2.VideoCapture(0)
    if camera.isOpened():
      isOkay = True
    else:
      self.logd("start", "Unable to open camera; will abort...")
    
    # * Final check before vision loop
    if not isOkay:
      return
    
    # * Create FrameProcessor objects, initialize supporting variables
    colorFilter = ColorFilterProcessor()
    fresh = True
    
    # * Processing loop
    timeStart = cv2.getTickCount() / cv2.getTickFrequency()
    timeLast = timeNow = 0.0
    while(1):
      # ** Timing: Obtain relative timestamp for this loop iteration
      timeNow = (cv2.getTickCount() / cv2.getTickFrequency()) - timeStart
      if showFPS:
        timeDiff = (timeNow - timeLast)
        fps = (1.0 / timeDiff) if (timeDiff > 0.0) else 0.0
        self.logd("start", "{0:5.2f} fps".format(fps))
      
      # ** Read frame from camera
      _, frame = camera.read()
      if showInput:
        cv2.imshow("Input", frame)
      
      # ** Initialize FrameProcessors, if required
      if(fresh):
        colorFilter.initialize(frame, timeNow) # timeNow should be zero on initialize
        fresh = False
      
      # ** Process frame
      keepRunning, imageOut = colorFilter.process(frame, timeNow)
      if showOutput and imageOut is not None:
        cv2.imshow("Output", imageOut)
      if not keepRunning:
        break
      
      # ** Process keyboard events with inter-frame delay
      key = cv2.waitKey(delay)
      if key != -1:
        keyCode = key & 0x00007f
        keyChar = chr(keyCode) if not (key & KeyCode.SPECIAL) else None
        
        if keyCode == 0x1b or keyChar == 'q':
          break
        elif not colorFilter.onKeyPress(key, keyChar):  # pass along key-press to FrameProcessor
          break
      
      # ** Timing: Save timestamp for fps calculation
        timeLast = timeNow
      
    # * Clean-up
    self.logd("start", "Cleaning up...")
    cv2.destroyAllWindows()
    camera.release()
  
  def logd(self, func, msg):
    if self.debug:
      log(self, func, msg)
    else:
      pass


def run(context):  # context is a dict with bot_loc, blocks, zones, corners, waypoints, etc.
  # Create VisionManager to handle shared data, start vision processors and main vision loop
  visManager = VisionManager(context)
  visManager.start()


if __name__ == "__main__":
  print "vision [warning]: Cannot start without bot context!"
  run({ })
