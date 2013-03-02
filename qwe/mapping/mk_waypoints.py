"""
The function mk_waypoints generates the waypoints.  It accepts the 'res' argument which is the map resolution in tiles per inch.  It also accepts the map_grid_vars dict which contains variables also needed in mk_map.  It returns the waypoints data structure.

"""



def mk_waypoints(res, map_grid_vars):

	"""
	Calculate Waypoints - these waypoints are for the flipped map
	"""

	#calculate waypoints
	# make data structure for waypoints
	#((grid_x,grid_y),(real_x,real_y), theta)
	waypoints = {}
	waypoints['land'] = ((1,2),(2,4),0)	#midpoint of land locations
	waypoints['sea'] = ((2,4),(8,16),0)	#midpoint of sea locations
	#waypoints['air']			#midpoint of air locations
	#waypoints['storage']			#midpoint of storage locations

	start_grid =  (map_grid_vars['wall']+map_grid_vars['startW']/2,map_grid_vars['wall']+map_grid_vars['startH']/2)		#(grid_x,grid_y)
	start_real = (start_grid[0]*res, start_grid[1]*res)	#(real_x,real_y)
	waypoints['start'] = (start_grid,start_real)	#center of start location
	#print(waypoints['start'])

	"""
	waypoints['St01']			#center of storage locations
	waypoints['St02']
	waypoints['St03']
	waypoints['St04']
	waypoints['St05']
	waypoints['St06']
	waypoints['St07']
	waypoints['St08']
	waypoints['St09']
	waypoints['St10']
	waypoints['St11']
	waypoints['St12']
	waypoints['St13']
	waypoints['St14']
	waypoints['A01']			#center of air locations
	waypoints['A02']
	waypoints['L01']			#center of land locations
	waypoints['L02']	
	waypoints['L03']
	waypoints['L04']
	waypoints['L05']
	waypoints['L06']
	"""
	sea01_grid = (map_grid_vars['wall'] + int(4.5/2*res), map_grid_vars['wall'] + int((12+0.5+8.5+0.5+2.5/2)*res))
	sea01_real = (sea01_grid[0]*res, sea01_grid[1]*res)
	waypoints['Se01'] = (sea01_grid, sea01_real)	#center of sea locations
	#print(waypoints['Se01'])

	"""
	waypoints['Se02']
	waypoints['Se03']
	waypoints['Se04']
	waypoints['Se05']
	waypoints['Se06']
	waypoints['UppPlt']			#center of upper platform
	waypoints['LwrPlt']			#center of lower platform
	"""
	return(waypoints)


