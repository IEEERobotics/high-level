"""
map2txt accepts the map from mk_map() and creates 5 txt files - one text file per element in TileProp class
"""
def map2txt(Map):
	print("map2txt")
	cols = len(Map[0]) #index of last column in matrix
	rows = len(Map)
	#open file map_desc in current directory
	map_desc = open('./map_desc.txt', 'w')	
	#write descr elements from map to txt file
	for x in xrange(0,int(rows)):
		for y in xrange(0,int(cols)):
			coord = Map[x][y].desc
			s = str(coord)
			map_desc.write(s)
			if y < (cols-1):
				map_desc.write(',')
			else :
				map_desc.write('\n')

	map_desc.close()

	#map_status = open()
	#map_color = open()
	#map_level = open()
	#map_path = open()

	return()
