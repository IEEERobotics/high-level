import numpy as np
import cv2
from cv2 import cv
import util as util
import random

#Make the back ground uniformly black
def getUniformBackGround(img, K):
	K1 = np.uint8(K*255)
	invK = 255 - K1
	_,bw = cv2.threshold(invK, 77, 255, cv2.THRESH_BINARY)
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
	_,whiteLines = cv2.threshold(white, 35, 255, cv2.THRESH_BINARY) #thresh = 35  works, but check
	
	#debug
	#cv2.imshow("sumImg1",sumImg)	
	#cv2.imshow("white",white)
	#cv2.imshow("white lines",whiteLines)
	
	return whiteLines
	

def drawRects(img, ctrs):
	i = 1
	rectList = []
	for ct in ctrs[0]:
		x, y, w, h = cv2.boundingRect(ct)

		#process only vertical rectagles (ie, w<h) with w and h > 1
		if w < h and w > 10 and h > 10:
			#print i, ". ", len(ct), " -- ", cv2.boundingRect(ct), (x+w/2), cv2.minAreaRect(ct)
			rectList.append([cv2.boundingRect(ct), cv2.minAreaRect(ct)])
			clr=(random.randrange(0,255),random.randrange(0,255),random.randrange(0,255))
			#cv2.drawContours(image=img, contours=ct, contourIdx=-1, color=clr , thickness=-1)
			cv2.rectangle(img, (x,y), (x+w,y+h), clr, 5)
			cv2.fillConvexPoly(img, ct, clr)
			cv2.rectangle(img, (x+w/2-3,y), (x+w/2+3,y+h), (255,255,255), -1)
			cv2.rectangle(img, (x,y+h/2-3), (x+w,y+h/2+3), (255,255,255), -1)
			#cv2.imshow("asdsdasdadasdasd",img)
			#key = cv2.waitKey(1000)
			i = i + 1
	cv2.rectangle(img, (318,0), (322,640), (255,255,255), -1)
	cv2.imshow("Output",img)
	print "done"
	return rectList
	

def process(img):
	C, M, Y, K = util.cvtColorBGR2CMYK_(img) #convert to CMYK
	imgNoBgnd = getUniformBackGround(img, K) #get uniform background
	whiteLines = getWhiteLines(C, M, Y, K) #get only white lines
	
	#remove white lines from image
	white3 = cv2.merge([whiteLines, whiteLines, whiteLines])
	imgBlocks = cv2.bitwise_and(imgNoBgnd, white3)
	
	#find the blocks in imgBlocks
	imgray = cv2.cvtColor(imgBlocks,cv.CV_RGB2GRAY);
	_,imbw = cv2.threshold(imgray, 20, 255, cv2.THRESH_BINARY_INV)
	ctrs = cv2.findContours(imbw, cv2.RETR_LIST , cv2.CHAIN_APPROX_SIMPLE);
	rectList = drawRects(img, ctrs)
	
	for i in range(len(rectList)):
		print rectList[i]
	
	#Process the CMYK of imgBlocks
	#The processing is necessary to find the color of the blocks.
	Cfinal, Mfinal, Yfinal, Kfinal = util.cvtColorBGR2CMYK_(imgBlocks) #convert 
	
	cfinal = np.uint8(Cfinal*255)
	_,cfinalbw = cv2.threshold(cfinal, 20, 255, cv2.THRESH_BINARY_INV)
	cv2.imshow("asdsd",cfinalbw)

	key = cv2.waitKey()



img = cv2.imread("pic10.jpg")
process(img)

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
