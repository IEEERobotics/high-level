"""Image preprocessing tools."""

from time import sleep
from util import Enum
from base import FrameProcessor
from main import main
import commands

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
  main(ExposureNormalizer(options=options))  # run an ExposureNormalizer instance using main.main()
