"""
Driver program for running a FrameProcessor.
Usage: main.py [<image filename>]
"""

import sys
import cv2
import pycv.base as base

# Script parameters
MyProcessor = base.FrameProcessor # which FrameProcessor to run
delay = 20 # inter-frame delay
showFPS = False # show fps?

def main():
    """Run a FrameProcessor on a static image (repeatedly) or on frames from a camera."""
    # TODO Accept video file as input
    
    # * Declare global (module) variables for proper write access
    global showFPS
    
    # * Initialize flags
    isOkay = False
    isStaticImage = False
    
    # * Read input image, if specified
    if len(sys.argv) >= 2:
        imageInFilename = sys.argv[1]
        print "main(): Reading image: \"" + imageInFilename + "\""
        frame = cv2.imread(imageInFilename)
        if frame is not None:
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
    processor = MyProcessor()
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
            cv2.imshow("Input", frame)
        
        # ** Initialize FrameProcessor, if required
        if(fresh):
            processor.initialize(frame, timeNow) # timeNow should be zero on initialize
            fresh = False
        
        # ** Process frame
        keepRunning, imageOut = processor.process(frame, timeNow)
        if imageOut is not None:
            cv2.imshow("Output", imageOut)
        if not keepRunning:
            break
        
        # ** Process keyboard events with inter-frame delay
        key = cv2.waitKey(delay)
        if key != -1:
            key &= 0xff # cv2.waitKey() returns an unexpectedly large number for a key-press, with the useful value in the last 8 bits
            ch = chr(key) if 0 <= key <= 255 else None
            #print "main(): key = {0}, ch = {1}".format(key, ch)
            if key == 0x1b or ch == ('q'):
                break
            elif ch == 'f':
                showFPS = not showFPS
        
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
