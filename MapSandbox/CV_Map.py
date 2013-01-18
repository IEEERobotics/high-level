"""
CV Map 
Ricker Snow

2-D map.  Will require angle calculations for ramp distance calculations.
"""

def mk_map():
	
	class TileProp:	#define a struct-like class
		desc = 0		#driving surface (0), start(1), storage(2), land(3), sea(4), air(5), marker/white line (7), wall(8)
		status = 0 		#empty(0), filled(1)
		color = 2		#unk(0), blue(1), black(2), green(3), yellow(4), red(5), brown(6)
		level = 0		# ground(0), ramp(1), lwr plat(2), upp plat(3)
		path = 0		#not path (0), path(1)


	tilesize = 16			#tiles per inch
	width = 97 * tilesize		# course width --> list index --> number of columns
	length = 73 * tilesize		#course length --> list number --> number of rows

	#Map[list number][list index] --> Map[row][col] --> Map[length][width]
	Map = [[TileProp() for x in xrange(0,int(width))] for y in xrange(0,int(length))]	# make a matrix with 		each element of class TileProp

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
		for y in xrange(0, upPltW):
			Map[x][y].level = 3
	#define upper ramp
	for x in xrange(0, upRmpL):
		for y in xrange(upPltW - 1, width - loPltW - 1):
			Map[x][y].level = 1
	#define lower platform
	for x in xrange(0, loPltL):
		for y in xrange(width - 1 - loPltW, width):
			Map[x][y].level = 2
	#define lower ramp
	for x in xrange(loPltL - 1, loPltL + loRmpL):
		for y in xrange(width - 1 - loRmpW, width):
			Map[x][y].level = 1

	"""walls"""
	#define long wall along width of course (south side)
	for x in xrange(length - wall - 1, length):
		for y in xrange(0, width):
			Map[x][y].desc = 8
	#define short wall along width of course (north side)
	for x in xrange(upPltL - 1, upPltL + wall):
		for y in xrange(0, upPltW + upRmpW):
			Map[x][y].desc = 8
	#define long wall along length of course (west side)
	for x in xrange(upPltL - 1, length):
		for y in xrange(0, wall):
			Map[x][y].desc = 8
	#short wall along length of course (east side)
	for x in xrange(loPltL + loRmpL, length):
		for y in xrange(width - wall, width):
			Map[x][y].desc = 8

	"""start area"""
	#start area - white outline - includes start area, next loop fixes enclosed area
	for x in xrange(length - 1 - wall - startL - whiteLine, length - wall):
		for y in xrange(wall, wall + startW + whiteLine):
			Map[x][y].desc = 7
	#start area - fix enclosed area
	for x in xrange(length - 1 - wall - startL, length - wall):
		for y in xrange(wall, wall + startW):
			Map[x][y].desc = 1

	"""air loading zone"""
	#air loading zone - white outline - includes enclosed space, next 2 loops fix
	for x in xrange(int(8.75*tilesize - 1), int((24-8.75)*tilesize)):
		for y in xrange(0, int(3.5*tilesize)):
			Map[x][y].desc = 7
	#air loading zone - fix enclosure - use two loops to account for seperating white line
	for x in xrange(int((8.75+.5)*tilesize - 1),int((8.75+0.5+2.5)*tilesize)):
		for y in xrange(0,3*tilesize):
			Map[x][y].desc = 5
	for x in xrange(int((8.75+.5+2.5+.5)*tilesize-1),int((24-8.75-0.5)*tilesize)):
		for y in xrange(0,3*tilesize):
			Map[x][y].desc = 5

	"""cargo area"""
	#cargo storage - white outline - includes enclosed area, next loop fixes
	for x in xrange(upPltL+wall-1, int(upPltL+wall+6.5*tilesize)):
		for y in xrange(int(wall+14.875*tilesize-1), int(wall+(14.875+42.5)*tilesize)):
			Map[x][y].desc = 7
	#fix enclosed storage area and make separating white lines
	k = 0
	m = wall + int((14.875+.5)*tilesize)
	#print("width=", width, "length=", length) #debug
	while k<=13:
		p = m + 3*tilesize*k
		#m = m + 3*tilesize*k
		for x in xrange(upPltL+wall-1, upPltL+wall+6*tilesize):
			for y in xrange(p-1,int(p+2.5*tilesize)):
				#print("k=", k,"m=", m, "x=", x, "y=", y) #debug
				Map[x][y].desc=2
				Map[x][y].color=0  #color unknown
		k = k + 1

	"""sea loading zone"""
	#white outline of sea loading zone
	for x in xrange(upPltL+wall+int(8.5*tilesize)-1, length-wall-int((12.5+8.5)*tilesize)):
		for y in xrange(0, int(4.5*tilesize)):
			Map[x][y].desc = 7
	#fix enclosed sea area and make seperating white lines
	k = 0
	m = upPltL + wall +int((8.5+.5)*tilesize)
	while k<=5:
		p = m + 3*tilesize*k
		#m = m + 3*tilesize*k
		for x in xrange(p-1, p + int(2.5*tilesize)):
			for y in xrange(wall - 1, wall + 4*tilesize):
				Map[x][y].desc = 4
				Map[x][y].color = 0
		k = k + 1

	"""land loading zone"""
	#white outline of land zone
	for x in xrange(length-wall-int(5.5*tilesize)-1,length - wall):
		for y in xrange(wall+int((12.5+31.75)*tilesize-1),width-wall-int(31.75*tilesize)):
			Map[x][y].desc = 7
	#fix enclosed land storage
	k = 0
	m = wall + int((12.5+31.75+.5)*tilesize)
	while k<=5:
		p = m + 3*tilesize*k
		#m = m+3*tilesize*k
		for x in xrange(length-wall-5*tilesize,length-wall):
			for y in xrange(p-1,p+int(2.5*tilesize)):
				Map[x][y].desc=3
				Map[x][y].color =0
		k = k+1
	return(Map)
