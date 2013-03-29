import numpy as np
 

class MapClass:
	def __init__(self, res, mapSize):
		self.res = res	
		self.mapSize = mapSize	
		self.scale = res
		# make a numpy 2D array
		self.grid = np.zeros(mapSize, dtype = [('desc', np.uint8),('status', '|S1'),('color', '|S1'),('level', '|S1'),('path', '|S1')])
	def ydim(self): 	#return the y dimension of grid (number of rows)
		return(len(self.grid))
	def xdim(self):		#return the x dimension of grid (number of columns)
		return(len(self.grid[0]))	
	def fillCoords(self, p1, p2, prop):	#fill an area defined by p1 and p2 with value prop['key'] in layer key of MyMap.grid
		x1,y1,x2,y2 = p1[0],p1[1],p2[0],p2[1]
		#calc range of y to fill over
		if y1 <= y2:	y_range = (y1, y2+1)	
		else: y_range = (y2, y1+1)
		#calc range of x to fill over
		if x1 <= x2: x_range = (x1, x2+1)
		else: x_range = (x2, x1+1)
		#now fill
		for y in xrange(y_range[0],y_range[1]):	
			for x in xrange(x_range[0],x_range[1]):
				for key in prop:
					self.grid[y][x][key] = prop[key]
	def fillLoc(self, locCenter, prop):
		midpt = (locCenter[0][0], locCenter[0][1])	#get center point to fill around
		xd = self.xdim()					#calc number of rows
		yd = self.ydim()					#calc number of columns
		#calc points that inscribe area to fill
		x1 = midpt[0] - int(2.5 / 2 * res)
		y1 = midpt[1] - int(2.5 / 2 * res)
		x2 = midpt[0] + int(2.5 / 2 * res)
		y2 = midpt[1] + int(2.5 / 2 * res)
		if x1 < 0: x1 = 0 	#check if p1 is out of bounds
		elif x1 >= xd: x1 = xd-1
		if y1 < 0: y1 = 0
		elif y1 >= yd: y1 = yd-1
		if x2 < 0: x2 = 0 	#check if p2 is out of bounds
		elif x2 >= xd: x2 = xd-1
		if y2 < 0: y2 = 0
		elif y2 >= yd: y2 = yd-1
		p1 = (x1, y1)
		p2 = (x2, y2)
		# call fill coords to fill area inscribed by p1 and p2		
		self.fillCoords(p1, p2, prop)
		 
		

