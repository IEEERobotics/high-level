import numpy as np
import cv2
from cv2 import cv
import commands
import time


capture = cv2.VideoCapture(0)

retval, frame = capture.read()
im1 = frame
im2 = frame

count = 0
while 1:
  #print "in while"
  #frame = cv.QueryFrame(capture)
    
  if count == 10:
    print commands.getstatusoutput('uvcdynctrl -s \'Exposure (Absolute)\' 1')
  if count == 20:
    print commands.getstatusoutput('uvcdynctrl -s \'Exposure (Absolute)\' 5')
    
  retval, frame = capture.read()
    
  if count == 19:
    print "Capturing 1.png"
    #cv2.imwrite("1.png", frame)
    im1 = frame
  if count == 29:
    print "Capturing 2.png"
    #cv2.imwrite("20.png", frame)
    im2 = frame
  if frame is None:
    break
  cv2.imshow('Camera', frame)
  k=cv.WaitKey(1);
  if k==27:
    break
  count = count + 1
    
cv2.imshow("1.png",im1)
cv2.imshow("2.png",im2)

im3 = im1/2 + im2/2
cv2.imshow("Avg,im3)
cv2.imwrite("1.png",im1)
cv2.imwrite("2.png",im2)
cv2.imwrite("avg.png", im3)

k=cv.WaitKey();
