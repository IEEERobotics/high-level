#Test

def mk_map_test():
	print("mkmap")
	class TileProp:	#define a struct-like class
		desc = 0		#driving surface (0), start(1), storage(2), land(3), sea(4), air(5), marker/white line (7), wall(8)
		status = 0 		#empty(0), filled(1)
		color = 2		#unk(0), blue(1), black(2), green(3), yellow(4), red(5), brown(6)
		level = 0		# ground(0), ramp(1), lwr plat(2), upp plat(3)
		path = 0		#not path (0), path(1)


	tilesize = 8			#tiles per inch
	width = 2 * tilesize		# course width --> list index --> number of columns
	length = 1 * tilesize		#course length --> list number --> number of rows

	#Map[list number][list index] --> Map[row][col] --> Map[length][width]
	Map = [[TileProp() for x in xrange(0,int(width))] for y in xrange(0,int(length))]	# make a matrix with 	each element of class TileProp

	return(Map)

