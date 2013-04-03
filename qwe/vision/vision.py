"""Vision module to manage different processors."""
# Usage: vision.py [<image/video filename>] [--gui] [--debug]

import sys
import argparse
import signal
import numpy as np

try:
  import cv2
  import cv2.cv as cv
except ImportError:
  print "You need OpenCV to use vision modules, sorry."
  sys.exit(1)

from util import KeyCode, isImageFile, log_str, rotateImage
from base import FrameProcessor, FrameProcessorPipeline
from colorfilter import ColorFilterProcessor
from blobdetection import CMYKBlobDetector
from blobtracking import BlobTracker
from linedetection import LineDetector
from linewalking import LineWalker
import logging.config

camera_frame_width = 640
camera_frame_height = 480
do_logging = True

class VisionManager:
  def __init__(self, bot_loc, blobs, blocks, zones, corners, waypoints, sc, bot_state, options=None, standalone=False):
    self.bot_loc = bot_loc
    self.blobs = blobs if blobs is not None else list()  # must be a list
    self.blocks = blocks
    self.zones = zones
    self.corners = corners
    self.waypoints = waypoints
    self.sc = sc
    self.bot_state = bot_state
    
    # * Set up logging
    if do_logging:
      logging.config.fileConfig('logging.conf')
      self.logger = logging.getLogger('vision')
    else:
      self.logger = None
    
    # * Get parameters and flags from options dict
    # ** Populate options first, if none given
    if options is None:
      parser = argparse.ArgumentParser(description="Vision manager.")
      parser.add_argument('filename', type=str, nargs='?', default=None, help="Image or video filename")
      parser.add_argument('--gui', action='store_true', help="Enable GUI mode (show images, process keyboard events)")
      parser.add_argument('--debug', action='store_true', help="Enable debug messages")
      parser.add_argument('--filter-bank', type=str, default=ColorFilterProcessor.defaultFilterBankFilename, help="Color filter bank to use")
      self.options = vars(parser.parse_args(args=None if standalone else []))  # if standalone, get options from command-line arguments, else set defaults
    else:
      self.options = options
    # ** Set option variables from options dict
    self.logi("__init__", "Options: " + str(self.options))
    self.filename = self.options['filename']
    self.gui = self.options['gui']
    self.debug = self.options['debug']
    
    # * [Sim] If standalone or navigator is not available otherwise, make self a simulator (to be passed along to processors)
    self.sim = False  # TODO get a reference to navigator to do line-walking
    self.heading = 0.0
  
  def start(self):
    """Create FrameProcessor objects and start vision loop (works on a static image, video or camera input)."""
    # * Initialize other parameters and flags
    delay = 10  # ms
    delayS = delay / 1000.0  # sec; only used in non-GUI mode, so this can be set to 0
    showInput = self.gui and True
    showOutput = self.gui and True
    showFPS = False
    showKeys = False
    
    isImage = False
    isVideo = False
    isReady = False
    isFrozen = False
    
    # * Read input image or video, if specified
    if self.filename is not None and not self.filename == "camera":
      if isImageFile(self.filename):
        self.logi("start", "Reading image: \"" + self.filename + "\"")
        frame = cv2.imread(self.filename)
        if frame is not None:
          if showInput:
            cv2.imshow("Input", frame)
          frozenFrame = frame.copy()  # useful if simulating and rotating image every frame
          isImage = True
          isReady = True
        else:
          self.loge("start", "Error reading image; fallback to camera.")
      else:
        self.logi("start", "Reading video: \"" + self.filename + "\"")
        camera = cv2.VideoCapture(self.filename)
        if camera.isOpened():
          isVideo = True
          isReady = True
        else:
          self.loge("start", "Error reading video; fallback to camera.")
  
    # * Open camera if input image/video is not provided/available
    if not isReady:
      self.logi("start", "Opening camera...")
      camera = cv2.VideoCapture(0)
      # ** Final check before vision loop
      if camera.isOpened():
        result_width = camera.set(cv.CV_CAP_PROP_FRAME_WIDTH, camera_frame_width)
        result_height = camera.set(cv.CV_CAP_PROP_FRAME_HEIGHT, camera_frame_height)
        self.logd("start", "Camera frame size set to {width}x{height} (result: {result_width}, {result_height})".format(width=camera_frame_width, height=camera_frame_height, result_width=result_width, result_height=result_height))
        isReady = True
      else:
        self.loge("start", "Error opening camera; giving up now.")
        return
    
    # * Create pipeline(s) of FrameProcessor objects, initialize supporting variables
    #pipeline = FrameProcessorPipeline(self.options, [ColorFilterProcessor, LineDetector, LineWalker])  # line walking pipeline
    pipeline = FrameProcessorPipeline(self.options, [CMYKBlobDetector])  # CMYK blob detection pipeline
    #pipeline = FrameProcessorPipeline(self.options, [ColorFilterProcessor, BlobTracker])  # blob tracking pipeline
    #pipeline = FrameProcessorPipeline(self.options, [ColorFilterProcessor, LineDetector, LineWalker, BlobTracker])  # combined pipeline
    # ** Get references to specific processors for fast access
    #colorFilter = pipeline.getProcessorByType(ColorFilterProcessor)
    lineWalker = pipeline.getProcessorByType(LineWalker)
    blobDetector = pipeline.getProcessorByType(CMYKBlobDetector)
    #blobTracker = pipeline.getProcessorByType(BlobTracker)
    
    # * Set signal handler before starting vision loop (NOTE must be done in the main thread of this process)
    signal.signal(signal.SIGTERM, self.handleSignal)
    signal.signal(signal.SIGINT, self.handleSignal)
    
    # * Vision loop
    self.logi("start", "Starting vision loop...")
    self.isOkay = True
    fresh = True
    frameCount = 0
    timeLast = timeNow = 0.0
    timeStart = cv2.getTickCount() / cv2.getTickFrequency()
    while self.isOkay:
      # ** [timing] Obtain relative timestamp for this loop iteration
      timeNow = (cv2.getTickCount() / cv2.getTickFrequency()) - timeStart
      
      # ** Print any pre-frame messages
      if not self.gui:
        self.logd("start", "[LOOP] Frame: {0:05d}, time: {1:07.3f}".format(frameCount, timeNow))  # if no GUI, print something to show we are running
      if showFPS:
        timeDiff = (timeNow - timeLast)
        fps = (1.0 / timeDiff) if (timeDiff > 0.0) else 0.0
        self.logi("start", "[LOOP] {0:5.2f} fps".format(fps))
      #self.logd("start", "Pipeline: " + str(pipeline))  # current state of pipeline (preceding ~ means processor is inactive)
      
      # ** If not static image, read frame from video/camera
      if not isImage and not isFrozen:
        isValid, frame = camera.read()
        if not isValid:
          break  # camera disconnected or reached end of video
        frameCount = frameCount + 1
        
        if showInput:
          cv2.imshow("Input", frame)
      
      # [Sim] Rotate image to simulate bot movement
      if self.sim and lineWalker is not None:
        if self.heading != 0.0:
          if isImage or isFrozen:
            frame = frozenFrame.copy()
          frame = rotateImage(frame, self.heading)
      
      # ** Initialize FrameProcessors, if required
      if(fresh):
        pipeline.initialize(frame, timeNow)
        fresh = False
      
      # TODO check bot_state activate only those processors that should be active
      
      # ** Process frame
      keepRunning, imageOut = pipeline.process(frame, timeNow)
      if not keepRunning:
        self.stop()
      
      # ** Perform post-process functions
      if blobDetector is not None:  # TODO check bot_state
        del self.blobs[:]
        self.blobs.extend(blobDetector.blobs)
        self.logd("start", "[LOOP] Got {0} blobs from blob detector".format(len(self.blobs)))
      
      # [Sim] Compute simulated bot movement from heading error reported by LineWalker
      # TODO Send out actual movement commands to navigator (only in LINE_WALKING state)
      if self.sim and lineWalker is not None:
        if lineWalker.state is LineWalker.State.GOOD and lineWalker.headingError != 0.0:
          #self.logd("start", "[LOOP] headingError: {0:6.2f}".format(lineWalker.headingError))
          self.heading -= 0.1 * lineWalker.headingError
      
      # ** Show output image
      if showOutput and imageOut is not None:
        cv2.imshow("Output", imageOut)  # output image from last processor
      
      # ** Check if GUI is available
      if self.gui:
        # *** If so, wait for inter-frame delay and process keyboard events using OpenCV
        key = cv2.waitKey(delay)
        if key != -1:
          keyCode = key & 0x00007f
          keyChar = chr(keyCode) if not (key & KeyCode.SPECIAL) else None
          
          if showKeys:
            self.logi("start", "Key: " + KeyCode.describeKey(key))
          
          if keyCode == 0x1b or keyChar == 'q':
            break
          elif keyChar == ' ':
            self.logi("start", "[PAUSED] Press any key to continue...")
            ticksPaused = cv2.getTickCount()  # [timing] save time when paused
            cv2.waitKey()  # wait indefinitely for a key press
            timeStart += (cv2.getTickCount() - ticksPaused) / cv2.getTickFrequency()  # [timing] compensate for duration paused
          elif keyCode == 0x0d:
            if not isImage:
              isFrozen = not isFrozen  # freeze frame, but keep processors running
              if isFrozen:
                frozenFrame = frame
              self.logi("start", "Frame {0:05d} is now frozen".format(frameCount) if isFrozen else "Frame processing unfrozen")
          elif keyChar == 'x':
            pipeline.deactivateProcessors()
            self.logi("start", "Pipeline processors deactivated.")
          elif keyChar == 'y':
            pipeline.activateProcessors()
            self.logi("start", "Pipeline processors activated.")
          elif keyChar == 'f':
            showFPS = not showFPS
          elif keyChar == 'k':
            showKeys = not showKeys
          else:
            keepRunning = pipeline.onKeyPress(key, keyChar)  # pass along key-press to processors in pipeline
            if not keepRunning:
              self.stop()
      
      # ** [timing] Save timestamp for fps calculation
      timeLast = timeNow
    
    # * Reset signal handlers to default behavior
    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    # * Clean-up
    self.logi("start", "Cleaning up...")
    if self.gui:
      cv2.destroyAllWindows()
    if not isImage:
      camera.release()
  
  def stop(self):
    self.isOkay = False  # request vision loop to stop (will be checked at the beginning of the next loop iteration)
  
  def handleSignal(self, signum, frame):
    if signum == signal.SIGTERM or signum == signal.SIGINT:
      self.logd("handleSignal", "Termination signal ({0}); stopping vision loop...".format(signum))
    else:
      self.loge("handleSignal", "Unknown signal ({0}); stopping vision loop anyways...".format(signum))
    self.stop()
  
  def loge(self, func, msg):
    #log(self, func, msg)
    outStr = log_str(self, func, msg)
    print outStr
    if self.logger is not None:
      self.logger.error(outStr)
  
  def logi(self, func, msg):
    #log(self, func, msg)
    outStr = log_str(self, func, msg)
    print outStr
    if self.logger is not None:
      self.logger.info(outStr)
  
  def logd(self, func, msg):
    #if self.debug:
    #  log(self, func, msg)
    outStr = log_str(self, func, msg)
    if self.debug:  # only used to filter messages to stdout, all messages are sent to logger if available
      print outStr
    if self.logger is not None:
      self.logger.debug(outStr)


def run(bot_loc=None, blobs=None, blocks=None, zones=None, corners=None, waypoints=None, sc=None, bot_state=None, options=None, standalone=False):
  """Entry point for vision process: Create VisionManager to handle shared data and start vision loop."""
  visManager = VisionManager(bot_loc=bot_loc, blobs=blobs, blocks=blocks, zones=zones, corners=corners, waypoints=waypoints, sc=sc, bot_state=bot_state, options=options, standalone=standalone)  # passing in shared data, options dict and stand-alone flag; use named arguments to avoid positional errors
  visManager.start()  # start vision loop


if __name__ == "__main__":
  print "Vision module (Warning: Cannot start properly without bot context!)"
  run(standalone=True)  # TODO pass in simulated shared memory structures
