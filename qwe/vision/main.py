"""
Driver program for running a FrameProcessor.
Usage: main.py [<image filename>]
"""

import sys
import cv2
from util import KeyCode
from base import FrameProcessor

def main(processorType=FrameProcessor, delay=20, showInput=True, showOutput=True, showFPS=False):
    """Run a FrameProcessor on a static image (repeatedly) or on frames from a camera."""
    # TODO Accept video file as input
    
    # * Initialize flags
    isOkay = False
    isStaticImage = False
    showKeys = False
    
    # * Read input image, if specified
    if len(sys.argv) >= 2:
        imageInFilename = sys.argv[1]
        print "main(): Reading image: \"" + imageInFilename + "\""
        frame = cv2.imread(imageInFilename)
        if frame is not None:
            if showInput:
              cv2.imshow("Input", frame)
            isStaticImage = True
            isOkay = True
        else:
            print "main(): Error reading image; fallback to camera."
    
    # * Open camera if not input image provided/available
    if not isStaticImage:
        print "main(): Opening camera..."
        camera = cv2.VideoCapture(0)
        isOkay = True
    
    # * Final check before processing loop
    if not isOkay:
        return
    
    # * Create FrameProcessor object, initialize supporting variables
    processor = processorType()
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
            print "main(): {0:5.2f} fps".format(fps)
        
        # ** If not static image, read frame from camera
        if not isStaticImage:
            _, frame = camera.read()
            if showInput:
                cv2.imshow("Input", frame)
        
        # ** Initialize FrameProcessor, if required
        if(fresh):
            processor.initialize(frame, timeNow) # timeNow should be zero on initialize
            fresh = False
        
        # ** Process frame
        keepRunning, imageOut = processor.process(frame, timeNow)
        if showOutput and imageOut is not None:
            cv2.imshow("Output", imageOut)
        if not keepRunning:
            break
        
        # ** Process keyboard events with inter-frame delay
        key = cv2.waitKey(delay)
        if key != -1:
            keyCode = key & 0x00007f  # key code is in the last 8 bits, pick 7 bits for correct ASCII interpretation (8th bit indicates 
            keyChar = chr(keyCode) if not (key & KeyCode.SPECIAL) else None # if keyCode is normal, convert to char (str)
            
            if showKeys:
                print "main(): " + KeyCode.describeKey(key)
                #print "main(): key = {key:#06x}, keyCode = {keyCode}, keyChar = {keyChar}".format(key=key, keyCode=keyCode, keyChar=keyChar)
            
            if keyCode == 0x1b or keyChar == 'q':
                break
            elif keyChar == 'f':
                showFPS = not showFPS
            elif keyChar == 'k':
                showKeys = not showKeys
            elif keyChar == 'i':
                showInput = not showInput
                if not showInput:
                    cv2.destroyWindow("Input")
            elif keyChar == 'o':
                showOutput = not showOutput
                if not showOutput:
                    cv2.destroyWindow("Output")
            elif not processor.onKeyPress(key, keyChar):
                break
        
        # TODO Implement pause on SPACE
        
        # ** Timing: Save timestamp for fps calculation
        timeLast = timeNow
    
    # * Clean-up
    print "main(): Cleaning up..."
    cv2.destroyAllWindows()
    if not isStaticImage:
        camera.release()
    
# Run main() function
if __name__ == "__main__":
    main()
