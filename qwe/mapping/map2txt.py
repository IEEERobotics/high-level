"""
Ricker Snow
map2txt() function accepts the map and creates 5 comma seperated txt files - one text file per key as described in CV_Map.py.  It starts filling the text file from the last row of the map data structure and ends with the first row of map.  Thus if map2txt is passed the map straight from mk_map() then the element in the first row and first column will correspond to the corner closest to the start area.  If map2txt is passed the map that has been processed by flip map then the data element in the first column and first row is the corner closest to the upper platform.
"""
def map2txt(Map):

	#print("map2txt")
	cols = len(Map.grid[0]) 	#find index of last column in matrix
	rows = len(Map.grid)		#find index of last row

	"""
	map_desc.txt
	"""
	#open file map_desc in current directory
	map_desc = open('./map_desc.txt', 'w')	

	#write descr elements from map to txt file
	#start writing from last row of Map and work to first row
	#this will make the element in the first row and first column of txt file 
	#correspond to the corner closest to start area
	last_row = rows-1	#index of last row
	y = last_row	
	while y >= 0:
		for x in xrange(0,int(cols)):	
			coord = Map.grid[y][x]['desc']
			s = str(coord)
			map_desc.write(s)
			#if not at the last column index, comma seperate adjacent data
			#else go to new line
			if x < (cols-1):
				map_desc.write(',')
			else :
				map_desc.write('\n')
		y = y-1

	#close map_desc.txt
	map_desc.close()

	"""
	map_status.txt
	"""
	#open file map_status in current directory
	map_status = open('./map_status.txt', 'w')
	
	#write status elements from map to txt file
	y = last_row
	while y >= 0:
		for x in xrange(0,int(cols)):
			coord = Map.grid[y][x]['status']
			s = str(coord)
			map_status.write(s)
			#if not at the last column index, comma seperate adjacent data
			#else go to new line
			if x < (cols-1):
				map_status.write(',')
			else :
				map_status.write('\n')
		y = y-1

	#close map_status.txt
	map_status.close()

	"""
	map_color.txt
	"""
	#open file map_color in current directory
	map_color = open('./map_color.txt', 'w')	
	#write color elements from map to txt file
	y = last_row
	while y >= 0:
		for x in xrange(0,int(cols)):
			coord = Map.grid[y][x]['color']
			s = str(coord)
			map_color.write(s)
			#if not at the last column index, comma seperate adjacent data
			#else go to new line
			if x < (cols-1):
				map_color.write(',')
			else :
				map_color.write('\n')
		y = y-1

	#close map_color.txt
	map_color.close()

	"""
	map_level.txt
	"""
	#open file map_level in current directory
	map_level = open('./map_level.txt', 'w')	
	#write level elements from map to txt file
	y = last_row
	while y >= 0:
		for x in xrange(0,int(cols)):
			coord = Map.grid[y][x]['level']
			s = str(coord)
			map_level.write(s)
			#if not at the last column index, comma seperate adjacent data
			#else go to new line
			if x < (cols-1):
				map_level.write(',')
			else :
				map_level.write('\n')
		y = y-1

	#close map_level.txt
	map_level.close()

	"""
	map_path.txt
	"""
	#open file map_path in current directory
	map_path = open('./map_path.txt', 'w')	
	#write path elements from map to txt file
	y = last_row
	while y >= 0:
		for x in xrange(0,int(cols)):
			coord = Map.grid[y][x]['path']
			s = str(coord)
			map_path.write(s)
			#if not at the last column index, comma seperate adjacent data
			#else go to new line
			if x < (cols-1):
				map_path.write(',')
			else :
				map_path.write('\n')
		y = y-1
	#close map_path.txt
	map_path.close()
	
	return()
