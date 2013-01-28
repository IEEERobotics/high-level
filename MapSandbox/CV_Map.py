"""
CV Map 
Ricker Snow

2-D map.  Will require angle calculations for ramp distance calculations.
First column and first row corresponds to top corner of upper most platform (near air storage is).  Last row first column corresponds to corner closest to start area.  The 'path' element of the map has not been set.
"""

def mk_map():
	#print("mk_map")
	class TileProp:			#define a struct-like class
		desc = 0		#driving surface (0), start(1), storage(2), land(3), sea(4), air(5), marker/white line (7), wall(8)
		status = 0 		#empty(0), filled(1)
		color = 2		#unk(0), blue(1), black(2), green(3), yellow(4), red(5), brown(6), white(7)
		level = 0		# ground(0), ramp(1), lwr plat(2), upp plat(3)
		path = 0		#not path (0), path(1)


	tilesize = 16			#tiles per inch
	width = 97 * tilesize		#course width --> list index --> number of columns
	length = 73 * tilesize		#course length --> list number --> number of rows

	# make a matrix with each element of class TileProp
	#Map[list number][list index] --> Map[row][col] --> Map[length][width]
	Map = [[TileProp() for x in xrange(0,int(width))] for y in xrange(0,int(length))]	

	# Variables
	upPltW = 24*tilesize			#Upper platform width
	upPltL = 24*tilesize			#Upper platform length
	upRmpW = 49*tilesize			#upper ramp width
	upRmpL = 24*tilesize			#upper ramp length
	loPltW = 24*tilesize			#lower platform width
	loPltL = 24*tilesize			#lower platform length
	loRmpW = 24*tilesize			#lower ramp width
	loRmpL = 24*tilesize			#lower ramp length
	wall = int(0.75 *tilesize)		#wall thickness
	whiteLine = int(0.5 * tilesize)		#thickness of white lines
	startW = 12 * tilesize			#start square width
	startL = 12 * tilesize			#start square length

	"""
	Begin initializing board, note that in definition of TileProp, everything is initialized to:
	empty, not path, black, driving surface, and ground level.
	"""
	#define upper platform
	for x in xrange(0,upPltL):	
		for y in xrange(0,upPltW):
			Map[x][y].level = 3	#upper platform
	#define upper ramp
	for x in xrange(0, upRmpL):
		for y in xrange(upPltW, width - loPltW):
			Map[x][y].level = 1	#ramp
	#define lower platform
	for x in xrange(0, loPltL):
		for y in xrange(width - loPltW, width):
			Map[x][y].level = 2	#lower platform
	#define lower ramp
	for x in xrange(loPltL, loPltL + loRmpL):
		for y in xrange(width - loRmpW, width):
			Map[x][y].level = 1	#ramp

	"""walls"""
	#define long wall along width of course (south side)
	for x in xrange(length - wall, length):
		for y in xrange(0, width):
			Map[x][y].desc = 8	#wall
	#define short wall along width of course (north side)
	for x in xrange(upPltL, upPltL + wall):
		for y in xrange(0, upPltW + upRmpW):
			Map[x][y].desc = 8	#wall
	#define long wall along length of course (west side)
	for x in xrange(upPltL, length):
		for y in xrange(0, wall):
			Map[x][y].desc = 8	#wall
	#short wall along length of course (east side)
	for x in xrange(loPltL + loRmpL, length):
		for y in xrange(width - wall, width):
			Map[x][y].desc = 8	#wall

	"""start area"""
	#start area - white outline - includes start area, next loop fixes enclosed area
	for x in xrange(length - wall - startL - whiteLine, length - wall):
		for y in xrange(wall, wall + startW + whiteLine):
			Map[x][y].desc = 7	#marker
			Map[x][y].color = 7	#white
	#start area - fix enclosed area
	for x in xrange(length - wall - startL, length - wall):
		for y in xrange(wall, wall + startW):
			Map[x][y].desc = 1	#start

	"""air loading zone"""
	#air loading zone - white outline - includes enclosed space, next 2 loops fix
	for x in xrange(int(8.75*tilesize), int((24-8.75)*tilesize)):
		for y in xrange(0, int(3.5*tilesize)):
			Map[x][y].desc = 7	#marker
			Map[x][y].color = 7	#white
	#air loading zone - fix enclosure - use two loops to account for seperating white line
	for x in xrange(int((8.75+.5)*tilesize),int((8.75+0.5+2.5)*tilesize)):
		for y in xrange(0,3*tilesize):
			Map[x][y].desc = 5	#air storage
			Map[x][y].color = 0	#color unknown
	for x in xrange(int((8.75+.5+2.5+.5)*tilesize),int((24-8.75-0.5)*tilesize)):
		for y in xrange(0,3*tilesize):
			Map[x][y].desc = 5	#air storage
			Map[x][y].color = 0	#color unknown

	"""cargo area"""
	#cargo storage - white outline - includes enclosed area, next loop fixes
	for x in xrange(upPltL+wall, int(upPltL+wall+6.5*tilesize)):
		for y in xrange(int(wall+14.875*tilesize), int(wall+(14.875+42.5)*tilesize)):
			Map[x][y].desc = 7	#marker
			Map[x][y].color = 7	#white
	#fix enclosed storage area and make separating white lines
	k = 0
	m = wall + int((14.875+.5)*tilesize)
	#print("width=", width, "length=", length) #debug
	while k<=13:
		p = m + 3*tilesize*k
		#m = m + 3*tilesize*k
		for x in xrange(upPltL+wall, upPltL+wall+6*tilesize):
			for y in xrange(p,int(p+2.5*tilesize)):
				#print("k=", k,"m=", m, "x=", x, "y=", y) #debug
				Map[x][y].desc=2	#cargo
				Map[x][y].color=0  	#color unknown
		k = k + 1

	"""sea loading zone"""
	#white outline of sea loading zone
	for x in xrange(upPltL+wall+int(8.5*tilesize), upPltL+wall+int((8.5+7*.5+6*2.5)*tilesize)):
		for y in xrange(wall, int(wall+4.5*tilesize)):
			Map[x][y].desc = 7	#marker
			Map[x][y].color = 7	#white
	#fix enclosed sea area and make seperating white lines
	k = 0
	m = upPltL + wall +int((8.5+.5)*tilesize)
	while k<=5:
		p = m + 3*tilesize*k
		#m = m + 3*tilesize*k
		for x in xrange(p, p + int(2.5*tilesize)):
			for y in xrange(wall, wall + 4*tilesize):
				Map[x][y].desc = 4	#sea 
				Map[x][y].color = 0	#color unknown
		k = k + 1

	"""land loading zone"""
	#white outline of land zone
	for x in xrange(length-wall-int(5.5*tilesize),length - wall):
		for y in xrange(wall+int((12.5+31.75)*tilesize),wall+int((12.5+31.75+6*2.5+7*.5)*tilesize)):
			Map[x][y].desc = 7	#marker
			Map[x][y].color = 7	#white
	#fix enclosed land storage
	k = 0
	m = wall + int((12.5+31.75+.5)*tilesize)
	while k<=5:
		p = m + 3*tilesize*k
		#m = m+3*tilesize*k
		for x in xrange(length-wall-5*tilesize,length-wall):
			for y in xrange(p,p+int(2.5*tilesize)):
				Map[x][y].desc=3	#land 
				Map[x][y].color =0	#color unknown
		k = k+1
	return(Map)
