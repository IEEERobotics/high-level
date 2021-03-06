"""Blob detection in CMYK + HSV color spaces."""

import random
import numpy as np

try:
  import cv2
  import cv2.cv as cv
except ImportError:
  print "You need OpenCV to use vision modules, sorry."
  sys.exit(1)

import util
from base import FrameProcessor
from main import main
from blobtracking import BlobTracker
from colors import colors, findMatchColorBGR

class SimpleBlob:
  colorBlue = (255, 0, 0)
  colorDarkBlue = (128, 64, 64)
  
  def __init__(self, area, bbox, rect, length, color_bgr, color):
    self.area = area
    self.bbox = bbox
    self.rect = rect
    self.center = (int(self.rect[0][0]), int(self.rect[0][1]))  # int precision is all we need
    self.size = self.rect[1]
    self.angle = self.rect[2]
    self.length = length
    self.color_bgr = color_bgr
    self.color = color
    
    #if self.size[0] > self.size[1]:
    #  self.size = (self.size[1], self.size[0])  # force it to be tall and narrow (for convenience)
    #  self.angle = (self.angle + 90) % 360
    
    #self.hypot = hypot(self.size[0], self.size[1])
    #self.aspect = self.size[0] / self.size[1]
    #self.rectArea = self.size[0] * self.size[1]
    #self.density = self.area / self.rectArea
    #self.lastCenter = None  # filled in when a matching blob is found from last frame
    #self.active = True
  
  def draw(self, imageOut):
    cv2.rectangle(imageOut, (self.bbox[0], self.bbox[1]), (self.bbox[0] + self.bbox[2], self.bbox[1] + self.bbox[3]), self.colorBlue, 2)
  
  def __str__(self):
    return "<SimpleBlob at ({center[0]:.2f}, {center[1]:.2f}), {length}, {color} ({color_bgr[2]:.2f}, {color_bgr[1]:.2f}, {color_bgr[0]:.2f})>".format(center=self.center, length=self.length, color=self.color, color_bgr=self.color_bgr)
  
  def detail(self):
    return "SimpleBlob: length: {length}, color: {color}, center: {center}, size: {size}, angle: {angle:.2f}, color_bgr: {color_bgr}".format(length=self.length, color=self.color, center=self.center, size=self.size, area=self.area, angle=self.angle, color_bgr=self.color_bgr)


def hsv(img):
  hsv = cv2.cvtColor(img,cv.CV_BGR2HSV)
  h,s,v=cv2.split(hsv)
  #cv2.imshow("hsv",hsv)
  #h = h - 100
  #s = s + 70
  #v = v + 50
  
  _,imbws = cv2.threshold(s, 60, 255, cv2.THRESH_BINARY_INV)
  _,imbwv = cv2.threshold(v, 100, 255, cv2.THRESH_BINARY)
  imbw = imbws & imbwv
  #cv2.imshow("imbws",imbws)
  #cv2.imshow("imbwv",imbwv)
  #cv2.imshow("imbw",imbw)
  s1 = cv2.bitwise_and(s, imbw)
  h1 = cv2.bitwise_and(h, imbw)
  v1 = cv2.bitwise_and(v, imbw)
  
  _, imBlackv = cv2.threshold(v, 200, 255, cv2.THRESH_BINARY_INV) #75
  #cv2.imshow("imBlackV", imBlackv)
  imBlack = 255-(imbws & imBlackv)
  #cv2.imshow("imBlack -- ", imBlack)
  
  imBlack3 = cv2.merge([imBlack, imBlack, imBlack])
  
  #cv2.imshow("h",h)
  #cv2.imshow("h1",h1)
  #cv2.imshow("s",s)
  #cv2.imshow("s1",s1)
  #cv2.imshow("v",v)
  #cv2.imshow("v1",v1)
  #s1 = s1 + 60
  final = cv2.merge((h1,s1,v1))
  #cv2.imshow("final",final)
  
  bgr = cv2.cvtColor(final, cv.CV_HSV2BGR)
  #cv2.imshow("ori", bgr)
  
  inv = cv2.bitwise_and(cv2.bitwise_not(bgr),img)
  inv = cv2.bitwise_and(inv,imBlack3)
  #cv2.imshow("oriinv", inv)
  
  return inv,bgr

def getColorsAndWhites(image):  # TODO debug this to replace hsv()
  # Split image into HSV components
  imageHSV = cv2.cvtColor(image, cv.CV_BGR2HSV)
  imageH, imageS, imageV = cv2.split(imageHSV)
  cv2.imshow("imageHSV", imageHSV)
  #imageH = imageH - 100
  #imageS = imageS + 70
  #imageV = imageV + 50
  
  # Compute saturation and value masks to filter out whites and blacks
  _, maskS = cv2.threshold(imageS, 60, 255, cv2.THRESH_BINARY_INV)  # low saturation
  _, maskV_white = cv2.threshold(imageV, 100, 255, cv2.THRESH_BINARY)  # high value
  _, maskV_black = cv2.threshold(imageV, 200, 255, cv2.THRESH_BINARY_INV)  # low value #75
  maskSV_white = maskS & maskV_white
  maskSV_black = maskS & maskV_black
  #cv2.imshow("maskS", maskS)
  #cv2.imshow("maskV_white", maskV_white)
  #cv2.imshow("maskV_black", maskV_black)
  #cv2.imshow("maskSV_white", maskSV_white)
  #cv2.imshow("maskSV_black", maskSV_black)
  
  # Obtain *whites* image
  imageH_masked = cv2.bitwise_and(imageH, maskSV_white)
  imageS_masked = cv2.bitwise_and(imageS, maskSV_white)
  imageV_masked = cv2.bitwise_and(imageV, maskV_white)
  #cv2.imshow("imageH", imageH)
  #cv2.imshow("imageH_masked", imageH_masked)
  #cv2.imshow("imageS", imageS)
  #cv2.imshow("imageS_masked", imageS_masked)
  #cv2.imshow("imageV", imageV)
  #cv2.imshow("imageV_masked", imageV_masked)
  #imageS_masked = imageS_masked + 60
  
  imageWhitesHSV = cv2.merge((imageH_masked, imageS_masked, imageV_masked))  # final whites image, HSV
  #cv2.imshow("imageWhitesHSV", imageWhitesHSV)
  imageWhites = cv2.cvtColor(imageWhitesHSV, cv.CV_HSV2BGR)  # final whites image, BGR
  #cv2.imshow("imageWhites", imageWhites)
  
  # Obtain *colors* image, i.e. pixels with good color content
  maskSV_noBlack = 255 - maskSV_black
  maskSV_noBlack_C3 = cv2.merge([maskSV_noBlack, maskSV_noBlack, maskSV_noBlack])  # 3-channel version of non-black mask
  imageColors = cv2.bitwise_and(cv2.bitwise_not(imageWhites), image)
  imageColors = cv2.bitwise_and(imageColors, maskSV_noBlack_C3)
  #cv2.imshow("imageColors", imageColors)
  
  #maskSV_noWhite = 255 - maskSV_white
  #maskSV_noWhite_C3 = cv2.merge([maskSV_noWhite, maskSV_noWhite, maskSV_noWhite])  # 3-channel version of non-white mask
  #mask_colors = cv2.bitwise_and(maskSV_noWhite_C3, maskSV_noBlack_C3)  # stuff that is not white and not black
  #imageColors = cv2.bitwise_and(image, mask_colors)
  
  return imageColors, imageWhites

def showHist(img,i):  # NOTE unused
  h = np.zeros((300,256,3))
  b,g,r = img[:,:,0],img[:,:,1],img[:,:,2]
  bins = np.arange(257)
  bin = bins[0:-1]
  color = [ (255,0,0),(0,255,0),(0,0,255) ]
  #print cv2.mean(b),"\t", cv2.mean(g),"\t", cv2.mean(r)
  for item,col in zip([b,g,r],color):
    N,bins = np.histogram(item,bins)
    v=N.max()
    N = np.int32(np.around((N*255)/v))
    N=N.reshape(256,1)
    pts = np.column_stack((bin,N))
    cv2.polylines(h,[pts],False,col,2)
  
  h=np.flipud(h)
  
  cv2.imshow("img--"+str(i),h)

  hsv = cv2.cvtColor(img,cv.CV_BGR2HSV)
  h,s,v=cv2.split(hsv)
  print cv2.mean(h),"\t", cv2.mean(s),"\t", cv2.mean(v)

def getUniformBackGround(img, K):  # NOTE unused
  """Make the background uniformly black."""
  K1 = np.uint8(K*255)
  invK = 255 - K1
  _,bw = cv2.threshold(invK, 50, 255, cv2.THRESH_BINARY) # 77 = 0.3 default , 50 - low light, other values = 40
  bw3 = cv2.merge([bw, bw, bw])
  imgNoBgnd = cv2.bitwise_and(img, bw3) #final in matlab
  
  #debug
  #cv2.imshow("ininvKK",invK)
  #cv2.imshow("bw",bw)
  #cv2.imshow("imgNoBgnd",imgNoBgnd)
  
  return imgNoBgnd

def getWhiteLines(C, M, Y, K):
  """Extract Only White Lines."""
  sumImg = np.uint8((C + M + Y + K)*255/4)
  white = cv2.erode(sumImg, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15,15))) # (10, 10) works
  _,whiteLines = cv2.threshold(white, 45, 255, cv2.THRESH_BINARY) #thresh = 35  works, other values: 25, 
  
  #debug
  #cv2.imshow("sumImg1",sumImg) 
  #cv2.imshow("white",white)
  #cv2.imshow("white lines",whiteLines)
  
  return whiteLines

def getRects(ctrs, imageOut=None):
  i = 1
  rectList = []
  #print "getRects(): {0} contours".format(len(ctrs[0]))
  for ct in ctrs[0]:
    #ct = ct.astype(np.int32)
    bbox = cv2.boundingRect(ct)
    x, y, w, h = bbox

    length = ""
    #process only vertical rectagles (ie, w<h) with w and h > 1
    if w < h and w > 30 and h > 70:
      #print i, ". ", len(ct), " -- ", cv2.boundingRect(ct), (x+w/2), cv2.minAreaRect(ct)
      
      #dist = 320-(x+w/2)
      #direction = 1
      #if dist < 0:
      #  direction = -1
      #print "Distance to center: ", dist, "pixels -- ", dist*0.0192, "inches --", dist*0.0192*1622/9.89,"revolutions"
      
      #if (x < 320) and ((x+w) > 320):
      if h > 173:
        length = "large"
      elif h > 140:
        length = "medium"
      elif h > 100:
        length = "small"
      #print i, " : ", cv2.boundingRect(ct), " -- ", length, "---", x, x+w, y, h
      
      #color detection code here... 
      color = "red"
      
      rectList.append([cv2.boundingRect(ct), cv2.minAreaRect(ct),length, color])
      
      if imageOut is not None:
        clr=(random.randrange(0,255),random.randrange(0,255),random.randrange(0,255))
        #cv2.drawContours(image=imageOut, contours=ct, contourIdx=-1, color=clr , thickness=-1)
        cv2.rectangle(imageOut, (x,y), (x+w,y+h), clr, 5)
        #cv2.fillConvexPoly(imageOut, ct, clr)
        cv2.rectangle(imageOut, (x+w/2-3,y), (x+w/2+3,y+h), (255,255,255), -1)
        cv2.rectangle(imageOut, (x,y+h/2-3), (x+w,y+h/2+3), (255,255,255), -1)
        rotRect = cv2.minAreaRect(ct)
        box = cv2.cv.BoxPoints(rotRect)
        box = np.int0(box)
        #print box
        #cv2.drawContours(imageOut, [box], 0, (0,0,255),2)
      
      i = i + 1
  
  if imageOut is not None:
    cv2.rectangle(imageOut, (318,0), (322,640), (255,255,255), -1)
    #cv2.imshow("Rects", imageOut)
  #print "done"
  
  ## sort rectList by the first tuple - so that they are from left to right in image.
  rectList.sort(key=lambda tup: tup[0])
  
  return rectList


class CMYKBlobDetector(FrameProcessor):
  """Detects blobs in using transformations in CMYK color space."""
  
  minBlobWidth = 20
  minBlobHeight = 70
  
  def __init__(self, options):
    FrameProcessor.__init__(self, options)
  
  def initialize(self, imageIn, timeNow):
    self.image = imageIn
    self.imageOut = None
    self.blobs = []
    self.active = True
  
  def process(self, imageIn, timeNow):
    self.image = imageIn
    if self.gui: self.imageOut = self.image.copy()
    
    self.blobs = []
    
    imageColors, imageWhites = hsv(self.image)
    if self.gui:
      cv2.imshow("imageColors", imageColors)
      cv2.imshow("imageWhites", imageWhites)
    
    C, M, Y, K = util.cvtColorBGR2CMYK_(imageWhites) #convert to CMYK
    #imgNoBgnd = getUniformBackGround(imageColors, K) #get uniform background
    #cv2.imshow("imgnobgnd", imgNoBgnd)
    invWhiteLines = getWhiteLines(C, M, Y, K) #get only white lines
    #cv2.imshow("White Lines", invWhiteLines)
    
    #remove white lines from imageColors
    invWhite3 = cv2.merge([invWhiteLines, invWhiteLines, invWhiteLines])
    #imgBlocks = cv2.bitwise_and(imgNoBgnd, invWhite3)
    imgBlocks = cv2.bitwise_and(imageColors, invWhite3)
    #imgBlocks = imageWhites
    #find the imageWhites in imgBlocks
    imgray = cv2.cvtColor(imgBlocks,cv.CV_RGB2GRAY);
    if self.gui:
      cv2.imshow("grayscale for imageWhites", imgray)
    _,imbw = cv2.threshold(imgray, 0, 255, cv2.THRESH_BINARY)
    if self.gui:
      cv2.imshow("bw for imageWhites", imbw)
    #cv2.imshow("imgBlocks", imgBlocks)
    
    # Contour processing: Old way
    '''
    ctrs = cv2.findContours(imbw, cv2.RETR_LIST , cv2.CHAIN_APPROX_SIMPLE);
    #imgCopy = imageColors
    
    rectList = getRects(ctrs, imageOut)
    self.logd("processBlobs", "{0} rects".format(len(rectList)))
    '''
    
    # Contour processing: New way
    # * Find contours
    contours, _ = cv2.findContours(imbw, cv2.RETR_LIST , cv2.CHAIN_APPROX_SIMPLE)
    
    # * Walk through list of contours
    for contour in contours:
      contour = contour.astype(np.int32)  # convert contours to 32-bit int for each individual contour
      
      # ** Compute blob properties to be used for filtering
      area = cv2.contourArea(contour)
      bbox = cv2.boundingRect(contour)
      x, y, w, h = bbox
      
      # ** Filter out ones that are too small or too big
      if area < BlobTracker.minBlobArea or area > BlobTracker.maxBlobArea: continue
      
      # ** Process only vertical rectangles (ie, w<h) with w and h > some threshold
      if w >= h or w <= self.minBlobWidth or h <= self.minBlobHeight: continue
      
      # ** Compute additional blob properties to be stored
      rect = cv2.minAreaRect(contour)
      
      length = "unknown"
      if h > 173:
        length = "large"
      elif h > 140:
        length = "medium"
      elif h > 100:
        length = "small"
      
      # ** Identify color (name)
      imageBlob = imgBlocks[y:y+h, x:x+w]
      #imageBlob = np.asarray(cv.GetSubRect(cv.fromarray(imgBlocks),rectList[i][0]))
      color_bgr = cv2.mean(imageBlob)
      color_obj = findMatchColorBGR(colors, color_bgr)
      #self.logd("process", "color_obj: {0}".format(color_obj))
      color = color_obj.name if color_obj is not None else "none"
      
      # ** Create blob object
      blob = SimpleBlob(area=area, bbox=bbox, rect=rect, length=length, color_bgr=color_bgr, color=color)
      
      # ** Apply additional filter(s) on computed blob properties  # NOTE density is not being calculated in SimpleBlob
      #if blob.density < BlobTracker.minBlobDensity: continue
      
      # ** Add to blobs list; TODO resolve with existing blob objects and update properties if a match is found?
      self.blobs.append(blob)
    
    # Blob drawing: Old way
    '''
    if self.gui:
      #print "B:\tG:\tR:"
      for i in range(len(rectList)):
        #print rectList[i]
        
        #(x,y),(w,h),t = rectList[i][1]
        #print x,y,w,h,t
        #x,y,w,h = rectList[i][0]
        
        
        cv2.imshow(str(i), imageBlob)
        #showHist(imageBlob, i)
        #print imageBlob.shape
        #rh,rw,rc = imageBlob.shape
        #print imageBlob[rh/2][rw/2][0],imageBlob[rh/2][rw/2][1],imageBlob[rh/2][rw/2][2]
        #Cfinal, Mfinal, Yfinal, Kfinal = util.cvtColorBGR2CMYK_(imageBlob)
        #print Cfinal[rh/2][rw/2],Mfinal[rh/2][rw/2],Yfinal[rh/2][rw/2],Kfinal[rh/2][rw/2]
        #hsv = cv2.cvtColor(imageBlob, cv.CV_BGR2HSV)
        #print hsv[rh/2][rw/2][0],hsv[rh/2][rw/2][1],hsv[rh/2][rw/2][2]
        #cv2.imshow('hsv'+str(i),hsv)
      #print "***********************"
    '''
    
    self.blobs.sort(key=lambda blob: blob.bbox)  # sort blob list by bbox (left-to-right, top-to-bottom, ...)
    
    # * Report and draw blobs
    self.logd("process", "{0} blobs".format(len(self.blobs)))
    for blob in self.blobs:
      self.logd("process", str(blob))  #blob.detail()
      if self.gui: blob.draw(self.imageOut)
    
    if self.gui:
      cv2.rectangle(self.imageOut, (318,0), (322,640), (255,255,255), -1)  # draw center line
    
    return True, self.imageOut


if __name__ == "__main__":
  options = { 'gui': True, 'debug': True }
  main(CMYKBlobDetector(options), options['gui'])
  '''
  #img = cv2.imread(filename)
  capture = cv2.VideoCapture(sys.argv[1] if len(sys.argv) > 1 else 0)
  
  count = 1
  while True:
    print "--------------------Frame", str(count),"-----------------------"
    count = count + 1
    
    retval, frame = capture.read()
    if frame is None:
      break
    cv2.imshow('Camera', frame)
    inv, blocks = hsv(frame)
    processBlocks(inv, blocks)
    
    k = cv.WaitKey()
    if k == 27:
      break
  
  cv2.waitKey()
  '''
