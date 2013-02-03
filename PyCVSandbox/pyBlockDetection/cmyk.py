import numpy as np
import cv2
from cv2 import cv
import util as util
import random


img = cv2.imread("pic10.jpg")
#cv2.imshow("Input",img)
#key = cv2.waitKey(1000)

#convert to CMY
C, M, Y, K = util.cvtColorBGR2CMYK_(img)
print "C", np.min(C), np.max(C)
print "M", np.min(M), np.max(M)
print "Y", np.min(Y), np.max(Y)
print "K", np.min(K), np.max(K)

#C = np.uint8(C*255)
#M = np.uint8(M*255) 
#Y = np.uint8(Y*255)
#K = np.uint8(K*255)

#debug
print "C", np.min(C), np.max(C)
print "M", np.min(M), np.max(M)
print "Y", np.min(Y), np.max(Y)
print "K", np.min(K), np.max(K)
cv2.imshow("C",C)
cv2.imshow("M",M)
cv2.imshow("Y",Y)
cv2.imshow("K",K)
#cv2.imwrite("cmyC.png",C)
#cv2.imwrite("cmyM.png",M)
#cv2.imwrite("cmyY.png",Y)
#cv2.imwrite("cmyK.png",K)

#threshold - remove black
K1 = np.uint8(K*255)
invK = 255 - K1
_,bw = cv2.threshold(invK, 77, 255, cv2.THRESH_BINARY)
bw3 = cv2.merge([bw, bw, bw])
imgNoBgnd = cv2.bitwise_and(img, bw3) #final in matlab

#debug
cv2.imshow("ininvKK",invK)
cv2.imshow("bw",bw)
cv2.imshow("imgNoBgnd",imgNoBgnd)


#remove white lines
#sumImg = np.uint8(C + M + Y + K)
#cv2.imshow("sumImg",sumImg)

sumImg = np.uint8((C + M + Y + K)*255/4)
cv2.imshow("sumImg1",sumImg)

white = cv2.erode(sumImg, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (10,10)))
cv2.imshow("white",white)
_,white = cv2.threshold(white, 35, 255, cv2.THRESH_BINARY) #fix 104 - needs to become a different number
cv2.imshow("white2",white)

#white = cv2.erode(white, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (10,10)))
#cv2.imshow("white",white)
#
white3 = cv2.merge([white, white, white])
imgBlocks = cv2.bitwise_and(imgNoBgnd, white3)

cv2.imshow("imgBlocks",imgBlocks)



Cfinal, Mfinal, Yfinal, Kfinal = util.cvtColorBGR2CMYK_(imgBlocks)
cfinal = np.uint8(Cfinal * 255)

cv2.imshow("CF",cfinal)
cv2.imshow("MF",Mfinal)
cv2.imshow("YF",Yfinal)
cv2.imshow("KF",Kfinal)

#cfinal = np.uint8(Cfinal)
_,cfinalbw = cv2.threshold(cfinal, 20, 255, cv2.THRESH_BINARY_INV)
cv2.imshow("asdsd",cfinalbw)

ctrs = cv2.findContours(cfinalbw, cv2.RETR_LIST , cv2.CHAIN_APPROX_SIMPLE);
print "Ctrs = ", len(ctrs)

i = 1
for ct in ctrs[0]:
	#print i, ". ", len(ct), " -- ", cv2.boundingRect(ct)
	x, y, w, h = cv2.boundingRect(ct)
	if w < h and w > 10 and h > 10:
		print i, ". ", len(ct), " -- ", cv2.boundingRect(ct), (x+w/2)
		clr=(random.randrange(0,255),random.randrange(0,255),random.randrange(0,255))
		#cv2.drawContours(image=img, contours=ct, contourIdx=-1, color=clr , thickness=-1)
		cv2.rectangle(img, (x,y), (x+w,y+h), clr, 5)
		cv2.rectangle(img, (x+w/2-3,y), (x+w/2+3,y+h), clr, -1)
		cv2.imshow("asdsdasdadasdasd",img)
		key = cv2.waitKey(100)
		i = i + 1
cv2.rectangle(img, (318,0), (322,640), (255,255,255), -1)
cv2.imshow("asdsdasdadasdasd",img)
print "done"

key = cv2.waitKey()


