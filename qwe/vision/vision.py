"""
Vision module to manage different processors.
Usage: vision.py [<image/video filename>]
"""

import sys
import numpy as np
import cv2
from util import KeyCode, isImageFile, log
from base import FrameProcessor
from colorfilter import ColorFilterProcessor
from blobtracking import BlobTracker

class VisionManager:
  def __init__(self, bot_loc, blocks, zones, corners, waypoints):
    self.bot_loc = bot_loc
    self.blocks = blocks
    self.zones = zones
    self.corners = corners
    self.waypoints = waypoints
    self.debug = True
  
  def start(self, filename=None):
    """Start main vision loop, running FrameProcessor instances on a static image, video or camera input."""
    # * Initialize parameters and flags
    delay = 10  # ms
    delayS = delay / 1000.0  # sec; only used in non-GUI mode, so this can be set to 0
    gui = True  # TODO pass gui flag to FrameProcessors and make them change their behavior accordingly (i.e. suppress imshows when gui == False)
    showInput = gui and True
    showOutput = gui and True
    showFPS = False
    showKeys = False
    
    isImage = False
    isVideo = False
    isOkay = False
    isFrozen = False
    
    # * Read input image or video, if specified
    if filename is not None:
      if isImageFile(filename):
        self.logd("start", "Reading image: \"" + filename + "\"")
        frame = cv2.imread(filename)
        if frame is not None:
          if showInput:
            cv2.imshow("Input", frame)
          isImage = True
          isOkay = True
        else:
          self.logd("start", "Error reading image; fallback to camera.")
      else:
        self.logd("start", "Reading video: \"" + filename + "\"")
        camera = cv2.VideoCapture(filename)
        if camera.isOpened():
          isVideo = True
          isOkay = True
        else:
          self.logd("start", "Error reading video; fallback to camera.")
  
    # * Open camera if input image/video is not provided/available
    if not isOkay:
      self.logd("start", "Opening camera...")
      camera = cv2.VideoCapture(0)
      # ** Final check before processing loop
      if camera.isOpened():
        isOkay = True
      else:
        self.logd("start", "Error opening camera; giving up now.")
        return
    
    # * Create FrameProcessor objects, initialize supporting variables
    colorFilter = ColorFilterProcessor()
    blobTracker = BlobTracker(colorFilter)
    frameProcessors = [colorFilter, blobTracker]
    fresh = True
    
    # * Processing loop
    timeStart = cv2.getTickCount() / cv2.getTickFrequency()
    timeLast = timeNow = 0.0
    while(1):
      # ** [timing] Obtain relative timestamp for this loop iteration
      timeNow = (cv2.getTickCount() / cv2.getTickFrequency()) - timeStart
      if showFPS:
        timeDiff = (timeNow - timeLast)
        fps = (1.0 / timeDiff) if (timeDiff > 0.0) else 0.0
        self.logd("start", "{0:5.2f} fps".format(fps))
      
      # ** If not static image, read frame from video/camera
      if not isImage and not isFrozen:
        isValid, frame = camera.read()
        if not isValid:
          break  # camera disconnected or reached end of video
        
        if showInput:
          cv2.imshow("Input", frame)
      
      # ** Initialize FrameProcessors, if required
      if(fresh):
        for frameProcessor in frameProcessors:
          frameProcessor.initialize(frame, timeNow) # timeNow should be zero on initialize
        fresh = False
      
      # ** Process frame
      keepRunning = True
      imageOut = None
      for frameProcessor in frameProcessors:
        keepRunning, imageOut = frameProcessor.process(frame, timeNow)
        if not keepRunning:
          break  # if a FrameProcessor signals us to stop, don't run others (break out of for loop)
      
      # ** Show output image
      if showOutput and imageOut is not None:
        cv2.imshow("Output", imageOut)  # output image from last FrameProcessor
      if not keepRunning:
        break  # if any FrameProcessor had signaled us to stop, we stop (break out of main processing loop)
      
      # ** Check if GUI is available
      if gui:
        # *** If so, wait for inter-frame delay and process keyboard events using OpenCV
        key = cv2.waitKey(delay)
        if key != -1:
          keyCode = key & 0x00007f
          keyChar = chr(keyCode) if not (key & KeyCode.SPECIAL) else None
          
          if showKeys:
            self.logd("process", "Key: " + KeyCode.describeKey(key))
          
          if keyCode == 0x1b or keyChar == 'q':
            break
          elif keyChar == ' ':
            self.logd("process", "[PAUSED] Press any key to continue...")
            ticksPaused = cv2.getTickCount()  # [timing] save time when paused
            cv2.waitKey()  # wait indefinitely for a key press
            timeStart += (cv2.getTickCount() - ticksPaused) / cv2.getTickFrequency()  # [timing] compensate for duration paused
          elif keyCode == 0x0d:
            isFrozen = not isFrozen  # freeze frame, but keep processors running
          elif keyChar == 'f':
            showFPS = not showFPS
          elif keyChar == 'k':
            showKeys = not showKeys
          else:
            keepRunning = True
            for frameProcessor in frameProcessors:
              keepRunning = frameProcessor.onKeyPress(key, keyChar)  # pass along key-press to FrameProcessor
              if not keepRunning:
                break  # break out of for loop
            if not keepRunning:
              break  # break out of main processing loop
      
      # ** [timing] Save timestamp for fps calculation
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


def run(bot_loc, blocks, zones, corners, waypoints):
  # Create VisionManager to handle shared data, start vision processors and main vision loop
  visManager = VisionManager(bot_loc, blocks, zones, corners, waypoints)
  visManager.start()


if __name__ == "__main__":
  print "vision: [warning] Cannot start without bot context!"
  #run(None, None, None, None, None)
  visManager = VisionManager(None, None, None, None, None)  # TODO pass in simulated shared memory structures
  visManager.start(sys.argv[1] if len(sys.argv) > 1 else None)
