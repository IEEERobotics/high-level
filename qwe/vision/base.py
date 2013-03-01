"""
Base classes for OpenCV-based computer vision.
"""

import numpy as np
import cv2
from util import log

class FrameProcessor:
    """Processes a sequence of images (frames)."""
    
    def __init__(self):
        self.debug = False # call base.FrameProcessor.__init__(self) and override self.debug
    
    def initialize(self, imageIn, timeNow):
        self.image = imageIn
        self.imageSize = (self.image.shape[1], self.image.shape[0])
        self.imageOut = self.image.copy()
        print "FrameProcessor.initialize(): Image size = " + str(self.imageSize)
        
    def process(self, imageIn, timeNow):
        self.image = imageIn
        self.imageOut = self.image
        return True, self.imageOut
    
    def onKeyPress(self, key, keyChar=None):
        return True
    
    def logd(self, func, msg):
        if self.debug:
            log(self, func, msg)
        else:
            pass
