"""
CV Map 
Ricker Snow

The mk_map function generates the map as it appears on sheet 7 of the course schematic; the element in the first column and first row corresponds to the corner closest to the upper platform.  mk_map accepts 'res' argument defining the resolution of the map in tiles per inch.  mk_map returns the map.


Notes:  Will require angle calculations for ramp distance calculations.  There may be some attributes we want to remove, like path and maybe status.  There's also redundancy between desc and color properties in that color contains white and desc contains markers/white lines.  This code is not optimized as it will not be used during bot runtime.  This code makes the map which will be stored as a pickled file or a text file.  The pickled file or text file will be brought back in to memory at bot runtime. 
"""
import numpy as np

def mk_map(res, map_grid_vars, map_prop_vars):

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

	mapSize = (map_grid_vars['height'], map_grid_vars['width']) # (height, width) --> (rows, cols)	
	myMap = MapClass(res,mapSize)


	"""
	Begin initializing board, everything is first initialized to:
	empty, not path, black, driving surface, and ground level.
	"""
	for y in xrange(0,map_grid_vars['height']):	
		for x in xrange(0,map_grid_vars['width']):
			myMap.grid[y][x]['level'] = map_prop_vars['ground']
			myMap.grid[y][x]['desc'] = map_prop_vars['driv_srfc']
			myMap.grid[y][x]['color'] = map_prop_vars['black']
			myMap.grid[y][x]['path'] = map_prop_vars['not_path']
			myMap.grid[y][x]['status'] = map_prop_vars['empty']
	#define upper platform
	for y in xrange(0,map_grid_vars['upPltH']):	
		for x in xrange(0,map_grid_vars['upPltW']):
			myMap.grid[y][x]['level'] = map_prop_vars['upp_plat']
	#define upper ramp
	for y in xrange(0, map_grid_vars['upRmpH']):
		for x in xrange(map_grid_vars['upPltW'], map_grid_vars['width'] - map_grid_vars['loPltW']):
			myMap.grid[y][x]['level'] = map_prop_vars['ramp']
	#define lower platform
	for y in xrange(0, map_grid_vars['loPltH']):
		for x in xrange(map_grid_vars['width'] - map_grid_vars['loPltW'], map_grid_vars['width']):
			myMap.grid[y][x]['level'] = map_prop_vars['lwr_plat']
	#define lower ramp
	for y in xrange(map_grid_vars['loPltH'], map_grid_vars['loPltH'] + map_grid_vars['loRmpH']):
		for x in xrange(map_grid_vars['width'] - map_grid_vars['loRmpW'], map_grid_vars['width']):
			myMap.grid[y][x]['level'] = map_prop_vars['ramp']
	#define edge between upper platform and ground and long ramp and ground
	y = map_grid_vars['upPltH'] - 1; 
	for x in xrange(0, map_grid_vars['upPltW'] + map_grid_vars['upRmpW'] + 1):
		#Map[x][y].level = 9
		myMap.grid[y][x]['desc'] = map_prop_vars['edge']
	#define edge between short ramp and ground
	x = map_grid_vars['upPltW'] + map_grid_vars['upRmpW']
	for y in xrange(map_grid_vars['loPltH'], (map_grid_vars['loPltH'] + map_grid_vars['loRmpH'])):
		#Map[x][y].level = 9
		myMap.grid[y][x]['desc'] = map_prop_vars['edge']

	"""walls"""
	#define long wall along width of course (south side)
	for y in xrange(map_grid_vars['height'] - map_grid_vars['wall'], map_grid_vars['height']):
		for x in xrange(0, map_grid_vars['width']):
			myMap.grid[y][x]['desc'] = map_prop_vars['wall']
	#define short wall along width of course (north side)
	for y in xrange(map_grid_vars['upPltH'], map_grid_vars['upPltH'] + map_grid_vars['wall']):
		for x in xrange(0, map_grid_vars['upPltW'] + map_grid_vars['upRmpW']):
			myMap.grid[y][x]['desc'] = map_prop_vars['wall']
	#define long wall along height of course (west side)
	for y in xrange(map_grid_vars['upPltH'], map_grid_vars['height']):
		for x in xrange(0, map_grid_vars['wall']):
			myMap.grid[y][x]['desc'] = map_prop_vars['wall']
	#short wall along height of course (east side)
	for y in xrange(map_grid_vars['loPltH'] + map_grid_vars['loRmpH'], map_grid_vars['height']):
		for x in xrange(map_grid_vars['width'] - map_grid_vars['wall'], map_grid_vars['width']):
			myMap.grid[y][x]['desc'] = map_prop_vars['wall']

	"""start area"""
	#start area - white outHine - includes start area, next loop fixes enclosed area
	for y in xrange(map_grid_vars['height'] - map_grid_vars['wall'] - map_grid_vars['startH'] - map_grid_vars['whiteLine'], map_grid_vars['height'] - map_grid_vars['wall']):
		for x in xrange(map_grid_vars['wall'], map_grid_vars['wall'] + map_grid_vars['startW'] + map_grid_vars['whiteLine']):
			myMap.grid[y][x]['desc'] = map_prop_vars['line']
			myMap.grid[y][x]['color'] = map_prop_vars['white']
	#start area - fix enclosed area
	for y in xrange(map_grid_vars['height'] - map_grid_vars['wall'] - map_grid_vars['startH'], map_grid_vars['height'] - map_grid_vars['wall']):
		for x in xrange(map_grid_vars['wall'], map_grid_vars['wall'] + map_grid_vars['startW']):
			myMap.grid[y][x]['desc'] = map_prop_vars['start']

	"""air loading zone"""
	#air loading zone - white outline - includes enclosed space, next 2 loops fix
	for y in xrange(map_grid_vars['upPlt_2_Air'], map_grid_vars['upPltH']-map_grid_vars['upPlt_2_Air']):
		for x in xrange(0, map_grid_vars['air_long']+map_grid_vars['whiteLine']):
			myMap.grid[y][x]['desc'] = map_prop_vars['line']
			myMap.grid[y][x]['color'] = map_prop_vars['white']
	#air loading zone - fix enclosure - use two loops to account for seperating white line
	for y in xrange(map_grid_vars['upPlt_2_Air']+map_grid_vars['whiteLine'], map_grid_vars['upPlt_2_Air']+map_grid_vars['whiteLine']+map_grid_vars['zone_short']):
		for x in xrange(0,map_grid_vars['air_long']):
			myMap.grid[y][x]['desc'] = map_prop_vars['air']	
			myMap.grid[y][x]['color'] = map_prop_vars['unk']	#color unknown
	for y in xrange(map_grid_vars['upPlt_2_Air']+map_grid_vars['whiteLine']+map_grid_vars['zone_short']+map_grid_vars['whiteLine'], map_grid_vars['upPltH']-map_grid_vars['upPlt_2_Air']-map_grid_vars['whiteLine']):
		for x in xrange(0,map_grid_vars['air_long']):
			myMap.grid[y][x]['desc'] = map_prop_vars['air']	
			myMap.grid[y][x]['color'] = map_prop_vars['unk']	#color unknown

	"""cargo area"""
	#cargo storage - white outline - includes enclosed area, next loop fixes
	for y in xrange(map_grid_vars['upPltH']+map_grid_vars['wall'], map_grid_vars['upPltH']+map_grid_vars['wall']+map_grid_vars['land_long']+map_grid_vars['whiteLine']):
		for x in xrange(map_grid_vars['wall']+map_grid_vars['edge2storage'], map_grid_vars['wall']+map_grid_vars['edge2storage']+map_grid_vars['cargoL']):
			myMap.grid[y][x]['desc'] = map_prop_vars['line']
			myMap.grid[y][x]['color'] = map_prop_vars['white']
	#fix enclosed storage area and make separating white lines
	k = 0	#variable to count the nth seperating line being implemented
	m = map_grid_vars['wall'] + map_grid_vars['edge2storage']+map_grid_vars['whiteLine']	#number of tiles until the first seperating white line
	#print("width=", width, "height=", height) #debug
	while k<=13:	#there are thirteen seperating lines (14 storage slots)
		p = m + map_grid_vars['air_long']*k
		#m = m + map_grid_vars['air_long']*k
		for y in xrange(map_grid_vars['upPltH']+map_grid_vars['wall'], map_grid_vars['upPltH']+map_grid_vars['wall']+map_grid_vars['stor_long']):
			for x in xrange(p,p+map_grid_vars['zone_short']):
				#print("k=", k,"m=", m, "x=", x, "y=", y) #debug
				myMap.grid[y][x]['desc'] = map_prop_vars['storage']
				myMap.grid[y][x]['color'] = map_prop_vars['unk']  	#color unknown
		k = k + 1

	"""sea loading zone"""
	#white outline of sea loading zone
	for y in xrange(map_grid_vars['upPltH']+map_grid_vars['wall']+map_grid_vars['EdgetoSea'], map_grid_vars['upPltH']+map_grid_vars['wall']+map_grid_vars['EdgetoSea']+map_grid_vars['seaH']):
		for x in xrange(map_grid_vars['wall'], map_grid_vars['wall']+map_grid_vars['sea_long']+map_grid_vars['whiteLine']):
			myMap.grid[y][x]['desc'] = map_prop_vars['line']
			myMap.grid[y][x]['color'] = map_prop_vars['white']
	#fix enclosed sea area and make seperating white lines
	k = 0	#variable to count the ntinth seperating line being implemented
	m = map_grid_vars['upPltH'] + map_grid_vars['wall']+map_grid_vars['EdgetoSea']+map_grid_vars['whiteLine']
	while k<=5:
		p = m + map_grid_vars['air_long']*k
		#m = m + map_grid_vars['air_long']*k
		for y in xrange(p, p + map_grid_vars['zone_short']):
			for x in xrange(map_grid_vars['wall'], map_grid_vars['wall'] + map_grid_vars['sea_long']):
				myMap.grid[y][x]['desc'] = map_prop_vars['sea']
				myMap.grid[y][x]['color'] = map_prop_vars['unk']	#color unknown
		k = k + 1

	"""land loading zone"""
	#white outline of land zone
	for y in xrange(map_grid_vars['height']-map_grid_vars['wall']-map_grid_vars['land_long']+map_grid_vars['whiteLine'], map_grid_vars['height'] - map_grid_vars['wall']):
		for x in xrange(map_grid_vars['wall']+map_grid_vars['startW']+map_grid_vars['whiteLine']+map_grid_vars['start2land'],map_grid_vars['wall']+map_grid_vars['startW']+map_grid_vars['whiteLine']+map_grid_vars['start2land']+map_grid_vars['landW']):
			myMap.grid[y][x]['desc'] = map_prop_vars['line']	#marker
			myMap.grid[y][x]['color'] = map_prop_vars['white']	#white
	#fix enclosed land storage
	k = 0
	m = map_grid_vars['wall'] + map_grid_vars['startW']+map_grid_vars['whiteLine']+map_grid_vars['start2land']+map_grid_vars['whiteLine']
	while k<=5:
		p = m + map_grid_vars['air_long']*k
		#m = m+map_grid_vars['air_long']*k
		for y in xrange(map_grid_vars['height']-map_grid_vars['wall']-map_grid_vars['land_long'],map_grid_vars['height']-map_grid_vars['wall']):
			for x in xrange(p,p+map_grid_vars['zone_short']):
				myMap.grid[y][x]['desc'] = map_prop_vars['land']	#land 
				myMap.grid[y][x]['color'] = map_prop_vars['unk']	#color unknown
		k = k+1

	
	return(myMap)
