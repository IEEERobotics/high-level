import numpy as np

try:
  import cv2
  from cv2 import cv
except ImportError:
  print "You need OpenCV to use vision modules, sorry."
  sys.exit(1)

import util as util
import random
import sys

#Make the back ground uniformly black
def getUniformBackGround(img, K):
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


#Extract Only White Lines
def getWhiteLines(C, M, Y, K):
	sumImg = np.uint8((C + M + Y + K)*255/4)
	white = cv2.erode(sumImg, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15,15))) # (10, 10) works
	_,whiteLines = cv2.threshold(white, 45, 255, cv2.THRESH_BINARY) #thresh = 35  works, other values: 25, 
	
	#debug
	#cv2.imshow("sumImg1",sumImg)	
	#cv2.imshow("white",white)
	#cv2.imshow("white lines",whiteLines)
	
	return whiteLines
	

def drawRects(img, ctrs):
	i = 1
	rectList = []
	for ct in ctrs[0]:
		print ct
		x, y, w, h = cv2.boundingRect(ct)

		#process only vertical rectagles (ie, w<h) with w and h > 1
		if w < h and w > 20 and h > 20:
			#print i, ". ", len(ct), " -- ", cv2.boundingRect(ct), (x+w/2), cv2.minAreaRect(ct)
			rectList.append([cv2.boundingRect(ct), cv2.minAreaRect(ct)])
			clr=(random.randrange(0,255),random.randrange(0,255),random.randrange(0,255))
			#cv2.drawContours(image=img, contours=ct, contourIdx=-1, color=clr , thickness=-1)
			cv2.rectangle(img, (x,y), (x+w,y+h), clr, 5)
			cv2.fillConvexPoly(img, ct, clr)
			cv2.rectangle(img, (x+w/2-3,y), (x+w/2+3,y+h), (255,255,255), -1)
			cv2.rectangle(img, (x,y+h/2-3), (x+w,y+h/2+3), (255,255,255), -1)
			
			rotRect = cv2.minAreaRect(ct)
			box = cv2.cv.BoxPoints(rotRect)
			box = np.int0(box)
			print box
			cv2.drawContours(img, [box], 0, (0,0,255),2)
			#cv2.imshow("asdsdasdadasdasd",img)
			#key = cv2.waitKey(1000)
			i = i + 1
	cv2.rectangle(img, (318,0), (322,640), (255,255,255), -1)
	cv2.imshow("Output",img)
	print "done"
	return rectList
	

def process(img, blocks):
	cv2.imshow("img", img)
	cv2.imshow("blocks", blocks)
	C, M, Y, K = util.cvtColorBGR2CMYK_(blocks) #convert to CMYK
	#imgNoBgnd = getUniformBackGround(img, K) #get uniform background
	#cv2.imshow("imgnobgnd", imgNoBgnd)
	invWhiteLines = getWhiteLines(C, M, Y, K) #get only white lines
	#cv2.imshow("White Lines", invWhiteLines)
	
	#remove white lines from image
	invWhite3 = cv2.merge([invWhiteLines, invWhiteLines, invWhiteLines])
	#imgBlocks = cv2.bitwise_and(imgNoBgnd, invWhite3)
	imgBlocks = cv2.bitwise_and(img, invWhite3)
	#imgBlocks = blocks
	#find the blocks in imgBlocks
	imgray = cv2.cvtColor(imgBlocks,cv.CV_RGB2GRAY);
	cv2.imshow("grayscale for blocks", imgray)
	_,imbw = cv2.threshold(imgray, 0, 255, cv2.THRESH_BINARY)
	cv2.imshow("bw for blocks", imbw)
	#cv2.imshow("img Blocks", imgBlocks)
	ctrs = cv2.findContours(imbw, cv2.RETR_LIST , cv2.CHAIN_APPROX_SIMPLE);
	#imgCopy = img
	rectList = drawRects(img, ctrs) #img
	
	
	#print "B:\tG:\tR:"
	for i in range(len(rectList)):
		print rectList[i]
		#print rectList[i][1]
		#(x,y),(w,h),t = rectList[i][1]
		#print x,y,w,h,t
		#x,y,w,h = rectList[i][0]
		
		rec = np.asarray(cv.GetSubRect(cv.fromarray(imgBlocks),rectList[i][0]))
		cv2.imshow(str(i), rec)
		#showHist(rec, i)
		#print rec.shape
		#rh,rw,rc = rec.shape
		#print rec[rh/2][rw/2][0],rec[rh/2][rw/2][1],rec[rh/2][rw/2][2]
		#Cfinal, Mfinal, Yfinal, Kfinal = util.cvtColorBGR2CMYK_(rec)
		#print Cfinal[rh/2][rw/2],Mfinal[rh/2][rw/2],Yfinal[rh/2][rw/2],Kfinal[rh/2][rw/2]
		#hsv = cv2.cvtColor(rec, cv.CV_BGR2HSV)
		#print hsv[rh/2][rw/2][0],hsv[rh/2][rw/2][1],hsv[rh/2][rw/2][2]
		#cv2.imshow('hsv'+str(i),hsv)
#print "***********************"


def showHist(img,i):
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

	
	
def hsv(img):
	hsv = cv2.cvtColor(img,cv.CV_BGR2HSV)
	h,s,v=cv2.split(hsv)
	#cv2.imshow("hsv",hsv)
	#h = h - 100
	#s = s + 70
	#v = v + 50
	
	_,imbws = cv2.threshold(s, 40, 255, cv2.THRESH_BINARY_INV) #was 60, 255
	_,imbwv = cv2.threshold(v, 100, 255, cv2.THRESH_BINARY)
	imbw = imbws & imbwv
	#cv2.imshow("imbws",imbws)
	#cv2.imshow("imbwv",imbwv)
	#cv2.imshow("imbw",imbw)
	s1 = cv2.bitwise_and(s, imbw)
	h1 = cv2.bitwise_and(h, imbw)
	v1 = cv2.bitwise_and(v, imbw)
	
	_, imBlackv = cv2.threshold(v, 75, 255, cv2.THRESH_BINARY_INV)
	#cv2.imshow("imBlackV", imBlackv)
	imBlack = 255-(imbws & imBlackv)
	cv2.imshow("imBlack -- ", imBlack)
	
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
	

#print sys.argv[1]
filename = "test1.png" #sys.argv[1]
img = cv2.imread(filename)
cv2.imshow("Original Image",img)
inv, blocks = hsv(img)
process(inv, blocks)
key = cv2.waitKey()
#debug
	#cv2.imshow("C",C)
	#cv2.imshow("M",M)
	#cv2.imshow("Y",Y)
	#cv2.imshow("K",K)
	#cv2.imshow("Img Uniform Background", imgNoBgnd)
	#cv2.imshow("White Lines", whiteLines)
	#cv2.imshow("Blocks without white lines",imgBlocks)

#debug
	#cv2.imshow("CF",Cfinal)
	#cv2.imshow("MF",Mfinal)
	#cv2.imshow("YF",Yfinal)
	#cv2.imshow("KF",Kfinal)

#cv2.imshow("imgray", imgray)
	#cv2.imshow("imbw", imbw)
	

#C = np.uint8(C*255)
#M = np.uint8(M*255) 
#Y = np.uint8(Y*255)
#K = np.uint8(K*255)
