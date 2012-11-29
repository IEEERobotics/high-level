"""
Base classes for OpenCV-based computer vision.
"""

import cv2

class FrameProcessor:
    """Processes a sequence of images (frames)."""
    
    def initialize(self, imageIn, timeNow):
        self.image = imageIn
        self.imageSize = (self.image.shape[1], self.image.shape[0])
        self.imageOut = self.image.copy()
        print "FrameProcessor.initialize(): Image size = " + str(self.imageSize)
        
    def process(self, imageIn, timeNow):
        self.image = imageIn
        
        self.imageOut = self.image
        return True, self.imageOut