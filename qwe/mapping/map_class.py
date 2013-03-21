import numpy as np

class MapClass:
	def __init__(self, res, mapSize):
		self.res = res	
		self.mapSize = mapSize	
		self.scale = res
		# make a numpy 2D array
		self.grid = np.zeros(mapSize, dtype = [('desc', np.uint8),('status', np.uint8),('color', np.uint8),('level', np.uint8),('path', np.uint8)])
	def ydim(self): 	#return the y dimension of grid (number of rows)
		return(len(self.grid))
	def xdim(self):		#return the x dimension of grid (number of columns)
		return(len(self.grid[0]))	
	def fill(self, p1, p2, prop):	#fill an area defined by p1 and p2 with value prop['key'] in layer key of MyMap.grid
		x1,y1,x2,y2 = p1[0],p1[1],p2[0],p2[1]
		if y1 <= y2:	y_range = (y1, y2)	
		else: y_range = (y2, y1)
		if x1 <= x2: x_range = (x1, x2)
		else: x_range = (x2, x1)
		for y in xrange(y_range[0],y_range[1]):	
			for x in xrange(x_range[0],y_range[1]):
				for key in prop:
					self.grid[y][x][key] = prop[key]

