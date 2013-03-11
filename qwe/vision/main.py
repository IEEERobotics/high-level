"""Driver program for running a single FrameProcessor."""
# Usage: main.py [<image/video filename>]

import sys
from time import sleep
import cv2
from util import KeyCode, isImageFile
from base import FrameProcessor

def main(processorType=FrameProcessor):
    """Run a FrameProcessor on a static image (repeatedly) or on frames from a camera/video."""
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
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        if isImageFile(filename):
            print "main(): Reading image: \"" + filename + "\""
            frame = cv2.imread(filename)
            if frame is not None:
                if showInput:
                    cv2.imshow("Input", frame)
                isImage = True
                isOkay = True
            else:
                print "main(): Error reading image; fallback to camera."
        else:
            print "main(): Reading video: \"" + filename + "\""
            camera = cv2.VideoCapture(filename)
            if camera.isOpened():
                isVideo = True
                isOkay = True
            else:
                print "main(): Error reading video; fallback to camera."
    
    # * Open camera if image/video is not provided/available
    if not isOkay:
        print "main(): Opening camera..."
        camera = cv2.VideoCapture(0)
        # ** Final check before processing loop
        if camera.isOpened():
            isOkay = True
        else:
            print "main(): Error opening camera; giving up now."
            return
    
    # * Create FrameProcessor object, initialize supporting variables
    processor = processorType()
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
            print "main(): {0:5.2f} fps".format(fps)
        
        # ** If not static image, read frame from video/camera
        if not isImage and not isFrozen:
            isValid, frame = camera.read()
            if not isValid:
                break  # camera disconnected or reached end of video
            
            if showInput:
                cv2.imshow("Input", frame)
        
        # ** Initialize FrameProcessor, if required
        if(fresh):
            processor.initialize(frame, timeNow) # timeNow should be zero on initialize
            fresh = False
        
        # ** Process frame
        keepRunning, imageOut = processor.process(frame, timeNow)
        
        # ** Show output image
        if showOutput and imageOut is not None:
            cv2.imshow("Output", imageOut)
        if not keepRunning:
            break  # if a FrameProcessor signals us to stop, we stop (break out of main processing loop)
        
        # ** Check if GUI is available
        if gui:
            # *** If so, wait for inter-frame delay and process keyboard events using OpenCV
            key = cv2.waitKey(delay)
            if key != -1:
                keyCode = key & 0x00007f  # key code is in the last 8 bits, pick 7 bits for correct ASCII interpretation (8th bit indicates 
                keyChar = chr(keyCode) if not (key & KeyCode.SPECIAL) else None # if keyCode is normal, convert to char (str)
                
                if showKeys:
                    print "main(): Key: " + KeyCode.describeKey(key)
                    #print "main(): key = {key:#06x}, keyCode = {keyCode}, keyChar = {keyChar}".format(key=key, keyCode=keyCode, keyChar=keyChar)
                
                if keyCode == 0x1b or keyChar == 'q':
                    break
                elif keyChar == ' ':
                    print "main(): [PAUSED] Press any key to continue..."
                    ticksPaused = cv2.getTickCount()  # [timing] save time when paused
                    cv2.waitKey()  # wait indefinitely for a key press
                    timeStart += (cv2.getTickCount() - ticksPaused) / cv2.getTickFrequency()  # [timing] compensate for duration paused
                elif keyCode == 0x0d:
                    isFrozen = not isFrozen  # freeze frame, but keep processors running
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
        else:
            # *** Else, wait for inter-frame delay using system method
            sleep(delayS)
        
        # ** [timing] Save timestamp for fps calculation
        timeLast = timeNow
    
    # * Clean-up
    print "main(): Cleaning up..."
    cv2.destroyAllWindows()
    if not isImage:
        camera.release()
    
# Run main() function
if __name__ == "__main__":
    main()
