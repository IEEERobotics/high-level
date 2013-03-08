#!/usr/bin/env python

"""
Records a video from the default camera for a specified duration using OpenCV.
Usage:
  camrecord.py [gui|nogui [<duration> [<video_filename>]]]
Video file: <video_filename>
Video data file (frame count, recorded duration, avg. fps): <video_filename>.dat
"""

import sys
import cv2
from time import sleep

maxDuration = 10.0  # sec
delay = 10  # ms
delayS = delay / 1000.0  # sec

camera = cv2.VideoCapture(0)
print "Opening camera..."
if not camera.isOpened():
  print "Error opening camera; aborting..."
  sys.exit(1)

videoFilename = None
video = None
dat = None
duration = maxDuration
gui = False

if len(sys.argv) > 1:
  gui = (sys.argv[1] == "gui")
  
  if len(sys.argv) > 2:
    duration = float(sys.argv[2])
  
  if len(sys.argv) > 3:
    videoFilename = sys.argv[3]
    print "Opening video file \"" + videoFilename + "\"..."
    video = cv2.VideoWriter(videoFilename, cv2.cv.CV_FOURCC('M', 'P', 'E', 'G'), 30, (640, 480))
    if not video.isOpened():
      print "Error opening video file; aborting..."
      sys.exit(1)
    
    datFilename = videoFilename + ".dat"
    print "Opening video data file \"" + datFilename + "\"..."
    dat = open(datFilename, 'w')

print "Main loop (GUI: {0}, duration: {1} secs., video file: {2})...".format(gui, duration, videoFilename)
frameCount = 0
fps = 0.0
timeStart = cv2.getTickCount() / cv2.getTickFrequency()
timeLast = timeNow = 0.0

while True:
  timeNow = (cv2.getTickCount() / cv2.getTickFrequency()) - timeStart
  
  timeDiff = (timeNow - timeLast)
  fps = (1.0 / timeDiff) if (timeDiff > 0.0) else 0.0
  #print "Frame %d: %5.2f fps" % (frameCount, fps)
  
  _, frame = camera.read()
  if frame is None:
    break
  
  if video is not None:
    video.write(frame)
  
  if gui:
    cv2.imshow("Camera", frame)
    key = cv2.waitKey(delay)
    if key != -1:
      break
  else:
    sleep(delayS)
  
  if timeNow > duration:
    break
  
  frameCount = frameCount + 1
  timeLast = timeNow

avgFPS = frameCount / timeNow
print "Done; %d frames, %.2f secs, %.2f fps" % (frameCount, timeNow, avgFPS)

if video is not None:
  print "Releasing video file..."
  video.release()
  
  if dat is not None:
    dat.write("{0} {1} {2}".format(frameCount, timeNow, avgFPS))
    print "Closing video data file..."
    dat.close()

print "Releasing camera..."
camera.release()
