"""
The function flip_map makes a mirror image of the map that is passed; the element in the first column and first row corresponds to the corner closest to the start area.  It accepts the map as an argument and returns the flipped map.

"""

def flip_map(Map):

	#cols = len(Map[0]) 	#number of columns
	rows = len(Map)		#number of rows

	row_sw1 = 0		#variable for switching rows
	row_sw2 = rows - 1	#2nd variable for switching rows
	count = rows/2		#number of times to perform row switching
	#print(Map[count])


	while (count > 0):	#switch rows to make a mirror image of the map
		row_tmp = Map[row_sw1].copy()	
		#print(row_tmp['desc'])
		row_tmp2 = Map[row_sw2].copy()	
		#print(row_tmp2['desc'])
		#print(Map[row_sw1]['desc'])
		Map[row_sw1] = row_tmp2	
		#print(Map[row_sw1]['desc'])
		Map[row_sw2] = row_tmp	
		#print(Map[row_sw2]['desc'])
		row_sw1 = row_sw1 + 1
		row_sw2 = row_sw2 - 1
		count = count - 1
		#print (Map['desc'])
		#print(count)


	return(Map)
