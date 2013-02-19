"""
White line detection.
For usage, see pycv.main module.
"""

import numpy as np
import cv2
from util import Enum
from base import FrameProcessor
from main import main

class Line:
    """Represents a line in 2D space."""
    
    def __init__(self, linePt1, linePt2):
        self.pt1 = linePt1
        self.pt2 = linePt2
        self.delta = np.subtract(self.pt2, self.pt1)
        self.m = float(self.delta[1]) / float(self.delta[0]) if self.delta[0] != 0.0 else (np.inf if self.delta[1] >=0 else -np.inf)
        self.c = self.pt1[1] - self.m * self.pt1[0]
        #print "delta = {0}, m = {1}, c = {2}".format(self.delta, self.m, self.c)

    def renderTo(self, imageOut):
        if np.isinf(self.m) or np.isinf(self.c):
            return
        
        dispPt1 = (0, int(self.c))
        dispPt2 = (imageOut.shape[1], int(self.m * imageOut.shape[1] + self.c))
        # TODO Clip points to imageOut, or rely on clipping in cv2.line()?    
        cv2.line(imageOut, dispPt1, dispPt2, (0, 255, 0), 2)


class LineDetector(FrameProcessor):
    """Detects thick white lines."""

    State = Enum(['INIT', 'ACTIVE', 'DONE', 'FAILED'])
    MIN_GOOD_FRAMES = 5
    MAX_BAD_FRAMES = 15
    
    def __init__(self):
        FrameProcessor.__init__(self)
        self.debug = True
        self.state = LineDetector.State.INIT
    
    def initialize(self, imageIn, timeNow):
        self.image = imageIn
        self.imageSize = (self.image.shape[1], self.image.shape[0]) # (width, height)
        self.imageOut = self.image.copy()
        self.goodFrames = 0
        self.badFrames = 0
        print "LineDetector.initialize(): Image size = " + str(self.imageSize)
        
        # Define corner template
        self.templateCorner = np.zeros((60, 60), np.uint8)
        self.templateCornerOffset = np.divide(self.templateCorner.shape, 2)
        cv2.rectangle(self.templateCorner, (0, 0), (40, 40), 255, cv2.cv.CV_FILLED)
        cv2.rectangle(self.templateCorner, (0, 0), (20, 20), 0, cv2.cv.CV_FILLED)
        cv2.imshow("Corner template", self.templateCorner)
        
        # TODO Define T template
        
        self.state = LineDetector.State.ACTIVE
        
    def process(self, imageIn, timeNow):
        #self.logd("process", "[{0}]".format(LineDetector.State.toString(self.state)));
        self.image = imageIn
        self.imageOut = self.image.copy()
        
        # * Obtain grayscale image
        #gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        #cv2.imshow("Gray", gray)
        
        # * Convert image to HSV space, and extract H, S, V channels
        imageHSV = cv2.cvtColor(self.image, cv2.COLOR_BGR2HSV_FULL)
        imageH, imageS, imageV = cv2.split(imageHSV)
        #cv2.imshow("Hue", imageH)
        #cv2.imshow("Sat", imageS)
        #cv2.imshow("Val", imageV)
        
        # * Apply saturation-value filter to extract white regions
        _, maskLowSat = cv2.threshold(imageS, 64, 255, cv2.THRESH_BINARY_INV)
        _, maskHighVal = cv2.threshold(imageV, 192, 255, cv2.THRESH_BINARY)
        #cv2.imshow("Low sat mask", maskLowSat)
        #cv2.imshow("High val mask", maskHighVal)
        maskWhite = cv2.bitwise_and(maskLowSat, maskHighVal)
        maskWhite = cv2.morphologyEx(maskWhite, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
        cv2.imshow("White mask", maskWhite)
        
        # * Convolve corner template over white mask to find corners
        methodMatchCorner = cv2.cv.CV_TM_SQDIFF_NORMED
        matchCorner = cv2.matchTemplate(maskWhite, self.templateCorner, methodMatchCorner)
        cv2.imshow("Corner match", matchCorner)
        
        # ** Find first corner
        minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(matchCorner)
        #print "minVal = {0}, maxVal = {1}, minLoc = {2}, maxLoc = {3}".format(minVal, maxVal, minLoc, maxLoc)
        bestLoc = minLoc if methodMatchCorner == cv2.cv.CV_TM_SQDIFF_NORMED else maxLoc
        bestLocCorrected = tuple(np.add(bestLoc, self.templateCornerOffset))
        cv2.circle(self.imageOut, bestLocCorrected, 25, (0, 255, 255), 2)
        linePt1 = bestLocCorrected
        
        # ** Occlude first corner region to find next
        cv2.circle(matchCorner, bestLoc, 25, 1.0, cv2.cv.CV_FILLED)
        minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(matchCorner)
        bestLoc = minLoc if methodMatchCorner == cv2.cv.CV_TM_SQDIFF_NORMED else maxLoc
        bestLocCorrected = tuple(np.add(bestLoc, self.templateCornerOffset))
        cv2.circle(self.imageOut, bestLocCorrected, 25, (255, 255, 0), 2)
        linePt2 = bestLocCorrected
        
        # TODO Abstract out bestLoc finding to a separate function to promote code reuse and extensibility
        # TODO Use corresponding value as a certainty measure
        
        # * Find a line passing through corners found
        self.primaryLine = Line(linePt1, linePt2)
        self.primaryLine.renderTo(self.imageOut)
        #cv2.line(self.imageOut, linePt1, linePt2, (0, 255, 0), 2)
        
        # * TODO Convolve T template to find T junctions, and line passing through them
        # * TODO Test which is more robust (corners vs T junctions) and pick one method
        
        # TODO Set state based on whether a consistent line was found or not (goodFrames >= MIN_GOOD_FRAMES);
        #   if too many frames have passed (badFrames > MAX_BAD_FRAMES), signal failure
        
        return True, self.imageOut


# Run a LineDetector instance using pycv.main.main()
if __name__ == "__main__":
    main(LineDetector)
