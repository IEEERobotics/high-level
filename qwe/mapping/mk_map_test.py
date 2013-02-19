#Test

#def mk_map_test():
	#print("mkmap_test")
class TileProp:	#define a struct-like class
	desc = 0		#driving surface (0), start(1), storage(2), land(3), sea(4), air(5), marker/white line (7), wall(8)
	status = 0 		#empty(0), filled(1)
	color = 0		#unk(0), blue(1), black(2), green(3), yellow(4), red(5), brown(6)
	level = 0		# ground(0), ramp(1), lwr plat(2), upp plat(3)
	path = 0		#not path (0), path(1)


tilesize = 8			#tiles per inch
width = 2 * tilesize		# course width --> list index --> number of columns
length = 1 * tilesize		#course length --> list number --> number of rows

#Map[list number][list index] --> Map[row][col] --> Map[length][width]
Map = [[TileProp() for x in xrange(0,int(width))] for y in xrange(0,int(length))]	# make a matrix with 	each element of class TileProp
row_swap1 = [[TileProp() for x in xrange(0,int(width))] for y in xrange(0,1)]
row_swap2 = [[TileProp() for x in xrange(0,int(width))] for y in xrange(0,1)]

	
	#return(Map)

"""Make map, initialize values, print, then switch rows """

#Map = mk_map_test()


# initialize values: row 0 has all zeros in desc, row 1 has all ones in desc, row 2 has all twos in desc...
new_desc = 1
for x in xrange(1,int(length)):
	for y in xrange(0, int(width)):
		Map[x][y].desc = new_desc
		Map[x][y].status = new_desc
		Map[x][y].color= new_desc
		Map[x][y].level = new_desc
		Map[x][y].path = new_desc
	new_desc = new_desc + 1


# print map
for x in xrange(0,int(length)):
	for y in xrange(0, int(width)):
		print Map[x][y].desc,

#switch rows
for x in xrange(0, length/2):
	row_swap1 = Map[x]
	row_swap2 = Map[length-1-x]
	Map[x] = row_swap2
	Map[length-1-x] = row_swap1

print('\n')
# print switched map
for x in xrange(0,int(length)):
	for y in xrange(0, int(width)):
		print Map[x][y].desc,
		
