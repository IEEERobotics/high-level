"""
Navigation along a white line using visual feedback.
"""

import numpy as np
import cv2
from util import rotateImage
from base import FrameProcessor
from main import main
from linedetection import Line, LineDetector

class LineWalker(FrameProcessor):
    """Navigates parallel to a white line boundary of a pickup/dropoff region."""

    def __init__(self):
        FrameProcessor.__init__(self)
        self.debug = True
    
    def initialize(self, imageIn, timeNow):
        #self.image = imageIn
        #self.imageSize = (self.image.shape[1], self.image.shape[0]) # (width, height)
        
        self.detector = LineDetector()
        self.detector.initialize(imageIn, timeNow)
        self.heading = 0.0  # degrees
    
    def process(self, imageIn, timeNow):
        #self.image = imageIn
        
        # [Sim] Turn imageIn by current angle = self.heading
        if self.heading != 0.0:
            #self.logd("process", "Heading = %.2f" % self.heading)
            imageIn = rotateImage(imageIn, self.heading)
        
        # Run LineDetector for one iteration
        keepRunning, imageOut = self.detector.process(imageIn, timeNow)
        
        # Grab detected line, if any (TODO Skip if not found / confidence is low)
        whiteLine = self.detector.primaryLine
        ptLeft = (0, int(whiteLine.c))
        ptRight = (imageOut.shape[1], int(whiteLine.m * imageOut.shape[1] + whiteLine.c))
        cv2.circle(imageOut, ptLeft, 10, (255, 0, 0), 2)
        cv2.circle(imageOut, ptRight, 10, (255, 0, 0), 2)
        
        # TODO Issue micro navigation commands to align self with line
        # [Sim] Artificially change self heading
        if abs(ptLeft[1] - ptRight[1]) < 5.0:
            pass
        elif ptLeft[1] < ptRight[1]:
            self.heading += 1.0
        else:
            self.heading -= 1.0
        
        # TODO Based on self.detector.state, iterate through move-check loop
        
        return keepRunning, imageOut
    
    def onKeyPress(self, key, keyChar=None):
        if keyChar == None:  # special key
            keyByte = key & 0xff
            
            if keyByte == 0x51:  # LEFT
                self.heading -= 1.0
            elif keyByte == 0x53:  # RIGHT
                self.heading += 1.0
        
        return True


# Run a LineWalker instance using pycv.main.main()
if __name__ == "__main__":
    main(LineWalker)
