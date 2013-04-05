"""Image preprocessing tools."""

from math import sqrt, hypot
import numpy as np
import cv2
from time import sleep
from util import Enum
from base import FrameProcessor
from main import main
import commands
from colorfilter import HSVFilter

blueFilter = HSVFilter(np.array([108, 70, 75], np.uint8), np.array([122, 255, 255], np.uint8))
brownFilter = HSVFilter(np.array([178, 128, 32], np.uint8), np.array([11, 255, 100], np.uint8))
whiteFilter = HSVFilter(np.array([0, 0, 100], np.uint8), np.array([179, 64, 255], np.uint8))
yellowFilter = HSVFilter(np.array([15, 100, 75], np.uint8), np.array([50, 255, 255], np.uint8))
greenFilter = HSVFilter(np.array([35, 70, 32], np.uint8), np.array([50, 255, 150], np.uint8))
redFilter = HSVFilter(np.array([175, 100, 75], np.uint8), np.array([15, 255, 255], np.uint8))

class Blob:
  colorBlue = (255, 0, 0)
  colorDarkBlue = (128, 64, 64)
  
  def __init__(self, tag, area, bbox, rect):
    self.tag = tag
    self.area = area
    self.bbox = bbox
    self.rect = rect
    
    self.center = (int(self.rect[0][0]), int(self.rect[0][1]))  # int precision is all we need
    self.size = self.rect[1]
    self.angle = self.rect[2]
  
  def draw(self, imageOut):
    cv2.rectangle(imageOut, (self.bbox[0], self.bbox[1]), (self.bbox[0] + self.bbox[2], self.bbox[1] + self.bbox[3]), self.colorBlue, 2)
  
  def __str__(self):
    return "<Blob {tag} at ({center[0]:.2f}, {center[1]:.2f}), size: ({size[0]:.2f}, {size[1]:.2f}, area: {area:0.2f})>".format(tag=self.tag, center=self.center, size=self.size, area=self.area)


class ColorPaletteDetector(FrameProcessor):
  """Tries to find a known color palette in camera view."""
  minBlobArea = 1000
  maxBlobArea = 6000
  paletteBBox = (0, 400, 640, 80)  # x, y, w, h
  
  markerTag0 = "blue"
  markerTag1 = "red"
  
  def __init__(self, options):
    FrameProcessor.__init__(self, options)
  
  def initialize(self, imageIn, timeNow):
    self.image = imageIn
    self.imageSize = (self.image.shape[1], self.image.shape[0])  # (width, height)
    self.imageCenter = (self.imageSize[0] / 2, self.imageSize[1] / 2)  # (x, y)
    self.imageOut = None
    self.active = True
    
    self.filterBank = dict(blue=blueFilter, brown=brownFilter, white=whiteFilter, yellow=yellowFilter, green=greenFilter, red=redFilter)
    self.masks = { }
    self.morphOpenKernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    self.blobs = list()
    self.paletteCenter = (320, 456)
    self.midPoint = (320, 456)
    self.cameraOffset = None
  
  def process(self, imageIn, timeNow):
    self.image = imageIn
    if self.gui: self.imageOut = self.image.copy()
    
    # * Initialize blobs
    self.blobs = list()
    
    # * Cut out expected palette area
    pbx, pby, pbw, pbh = self.paletteBBox
    self.imagePalette = self.image[pby:pby + pbh, pbx:pbx + pbw]
    if self.gui:
      cv2.imshow("Color palette", self.imagePalette)
      #self.imagePaletteOut = self.imageOut[pby:pby + pbh, pbx:pbx + pbw]
      cv2.rectangle(self.imageOut, (pbx, pby), (pbx + pbw, pby + pbh), (255, 0, 0))
    
    # * Get HSV
    self.imagePaletteHSV = cv2.cvtColor(self.imagePalette, cv2.COLOR_BGR2HSV)
    
    # * Apply filters
    for filterName, colorFilter in self.filterBank.iteritems():
      mask = colorFilter.apply(self.imagePaletteHSV)
      # ** Smooth out mask and remove noise
      mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.morphOpenKernel, iterations=2)
      self.masks[filterName] = mask
      if self.gui: cv2.imshow(filterName, self.masks[filterName])
      
      # ** Detect contours in mask
      contours, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE, offset=(pbx, pby))
      if len(contours) > 0:
        #self.logd("process", "[%.2f] %d %s contour(s)" % (timeNow, len(contours), maskName))  # report contours found
        #if self.gui and self.debug: cv2.drawContours(self.imageOut, contours, -1, (0, 255, 255))  # draw all contours found
        
        # *** Walk through list of contours
        for contour in contours:
          contour = contour.astype(np.int32)  # convert contours to 32-bit int for each individual contour [Pandaboard OpenCV bug workaround]
          
          # **** Filter out ones that are too small or too big
          area = cv2.contourArea(contour)
          if area < self.minBlobArea or area > self.maxBlobArea: continue
          
          # **** Create blob
          bbox = cv2.boundingRect(contour)
          rect = cv2.minAreaRect(contour)
          blob = Blob(filterName, area, bbox, rect)
          self.blobs.append(blob)
          blob.draw(self.imageOut)
    
    # * Report blobs found
    #if self.blobs:
    #  self.logd("process", "{0} blobs found:\n{1}".format(len(self.blobs), "\n".join((str(blob) for blob in self.blobs))))
    
    # * Get a handle on marker blobs (and make sure their relative positions are as expected)
    marker0 = self.getNearestBlob(self.markerTag0)
    marker1 = self.getNearestBlob(self.markerTag1)
    #self.logd("process", "Marker 0: {0}".format(marker0))
    #self.logd("process", "Marker 1: {0}".format(marker1))
    
    # * Compute midpoint and report X, Y offset
    if marker0 is not None and marker1 is not None:
      self.midPoint = (int((marker0.center[0] + marker1.center[0]) / 2), int((marker0.center[1] + marker1.center[1]) / 2))
      self.cameraOffset = (self.midPoint[0] - self.paletteCenter[0], self.midPoint[1] - self.paletteCenter[1])
      #self.logd("process", "Mid-point: {0}, camera offset: {1}".format(self.midPoint, self.cameraOffset))
      if self.gui:
        cv2.line(self.imageOut, marker0.center, marker1.center, (255, 0, 255), 2)
        cv2.circle(self.imageOut, self.midPoint, 5, (0, 255, 0), -1)
    else:
      self.cameraOffset = None
      #self.loge("process", "Couldn't determine mid-point and camera offset!")
    
    # * TODO Compute average color of brown and green patches to calibrate
    
    return True, self.imageOut
  
  def getBlobs(self, tag=None):
    """Return a generator/list for blobs that match given tag (or all, if not given)."""
    if tag is not None:
      return (blob for blob in self.blobs if blob.tag == tag)
    else:
      self.blobs
  
  def getNearestBlob(self, tag=None, point=None, maxDist=np.inf, minArea=minBlobArea):
    if point is None: point = self.imageCenter
    minDist = maxDist
    nearestBlob = None
    for blob in self.getBlobs(tag):
      dist = hypot(blob.center[0] - point[0], blob.center[1] - point[1])
      if dist < minDist:
        minDist = dist
        nearestBlob = blob
    return nearestBlob
  

class ExposureNormalizer(FrameProcessor):
  """Obtains a normalized image by averaging two images taken at different exposures."""
  State = Enum(['NONE', 'START', 'SAMPLE_LOW', 'SAMPLE_HIGH', 'DONE'])
  
  sample_time_low = 2.0  # secs; when to sample low-exposure image (rel. to start)
  sample_time_high = 4.0  # secs; when to sample high-exposure image (rel. to start)
  exposure_low = 1
  exposure_high = 5
  exposure_normal = 3
  loop_delay = None  # duration to sleep for every iteration (not required for camera); set to None to prevent sleeping
  
  def __init__(self, options):
    FrameProcessor.__init__(self, options)
    if self.debug:
      self.loop_delay = 0.025  # set some delay when debugging, in case we are running a video
    self.state = ExposureNormalizer.State.NONE  # set to NONE here, call start() to run through once
  
  def initialize(self, imageIn, timeNow):
    self.image = imageIn
    self.timeStart = self.timeDone = timeNow
    
    self.imageLow = self.imageHigh = self.imageOut = self.image  # use first given frame as default
    self.active = True
  
  def process(self, imageIn, timeNow):
    self.image = imageIn
    
    if self.state is ExposureNormalizer.State.START:
      self.timeStart = timeNow
      self.imageOut = self.image  # default output, till we get a better image
      self.setExposure(self.exposure_low)  # set exposure to low
      self.state = ExposureNormalizer.State.SAMPLE_LOW  # [transition]
    elif self.state is ExposureNormalizer.State.SAMPLE_LOW:
      if (timeNow - self.timeStart) >= self.sample_time_low:
        self.imageLow = self.image  # save low-exposure image
        self.imageOut = self.image  # update output with current image (still not the average)
        self.setExposure(self.exposure_high)  # set exposure to high
        self.state = ExposureNormalizer.State.SAMPLE_HIGH  # [transition]
    elif self.state is ExposureNormalizer.State.SAMPLE_HIGH:
      if (timeNow - self.timeStart) >= self.sample_time_high:
        self.imageHigh = self.image  # save high-exposure image
        self.imageOut = (self.imageLow / 2) + (self.imageHigh / 2)  # compute average image
        self.timeDone = timeNow  # so that we can tell whether the avg. image is stale or not
        self.setExposure(self.exposure_normal)  # set exposure back to normal
        self.state = ExposureNormalizer.State.DONE  # [transition]
        self.logd("process", "[DONE]")
    
    if self.loop_delay is not None:
      sleep(self.loop_delay)
    return True, self.imageOut  # always return imageOut, initially the same as input image at start()
  
  def onKeyPress(self, key, keyChar):
    if keyChar == 's':  # press 's' to start
      self.start()
    return True
  
  def start(self):
    self.logi("start", "Starting exposure-based normalization...")
    self.state = ExposureNormalizer.State.START
  
  def setExposure(self, value=3):
    status, output = commands.getstatusoutput("uvcdynctrl -s \"Exposure (Absolute)\" {value}".format(value=value))
    self.logd("setExposure", "[{state}] value: {value}, status: {status}, output:\n'''\n{output}\n'''".format(state=ExposureNormalizer.State.toString(self.state), value=value, status=status, output=output))
    return (status == 0)  # return whether successful or not


if __name__ == "__main__":
  options = { 'gui': True, 'debug': True }
  #main(ExposureNormalizer(options=options))  # run an ExposureNormalizer instance using main.main()
  main(ColorPaletteDetector(options=options))
