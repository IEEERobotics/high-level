import numpy as np
import map_vars as mvars
 

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
		xd = self.xdim()			#calc number of rows
		yd = self.ydim()			#calc number of columns
		x1,y1,x2,y2 = p1[0],p1[1],p2[0],p2[1]
		if (x1<0) or (x2<0) or (y1<0) or (y2<0): 
			print("Mapping Dimension Error 1")
			return()
		if (x1>=xd) or (x2>=xd) or (y1>=yd) or (y2>=yd): 
			print("Mapping Dimension Error 2")
			return()
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
	def fillLoc(self, key, prop):	#fill a location in a layer with a value (both given by prop dict).  The location to be filled is identified by key (key comes from waypoints['key'], i.e. key could be "L01")
		x = waypoints[key][0][0]	# get x and y coords of location
		y = waypoints[key][0][1]
		if key[0] is "L": 			#key is a land location
			
			x1 = int(x + 1.5/2*res)		#blocks are 1.5 in wide
			y1 = int(y - mvars.map_grid_vars['offset'] - mvars.map_grid_vars['whiteLine'])
			x2 = int(x - 1.5/2*res)
			y2 = int(y1 - 4*res +1)		#land blocks are 4 in long
		elif key[0] is "A":			#Air
			x1 = int(x - mvars.map_grid_vars['offset']- mvars.map_grid_vars['whiteLine'])
			y1 = int(y + 1.5/2*res) 	#blocks are 1.5 in wide
			x2 = int(x1 - 2*res +1)	#air blocks are 2 in long
			y2 = int(y - 1.5/2*res)
		elif key[1] is "e":			#Sea
			x1 = int(x - mvars.map_grid_vars['offset']- mvars.map_grid_vars['whiteLine'])
			y1 = int(y + 1.5/2*res) 	#blocks are 1.5 in wide
			x2 = int(x1 - 3*res +1)	#sea blocks are 3 in long
			y2 = int(y - 1.5/2*res)
		else:					#storage
			x1 = int(x + 1.5/2*res)		#blocks are 1.5 in wide
			y1 = int(y + mvars.map_grid_vars['offset'] + mvars.map_grid_vars['whiteLine'])
			x2 = int(x - 1.5/2*res)
			y2 = int(y1 + 4*res - 1)		#use all land blocks to fill storage
		#prepare points to send to fillCoords
		p1 = (x1, y1)
		p2 = (x2, y2)
		self.fillCoords(p1, p2, prop)
		 
		

