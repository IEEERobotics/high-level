"""
The function mk_waypoints generates the waypoints.  It accepts the 'res' argument which is the map resolution in tiles per inch.  It also accepts the map_grid_vars dict which contains variables also needed in mk_map.  It returns the waypoints data structure.

"""
import numpy as np


def mk_waypoints(res, map_grid_vars):

	"""
	Calculate Waypoints - these waypoints are for the flipped map
	"""
	# make dict for waypoints
	waypoints = {}	#waypoints['key']=((grid_x,grid_y),(real_x,real_y), theta)

	#calculate x and y values for land
	land_grid_x = int(map_grid_vars['wall']+map_grid_vars['startW']+4.5*map_grid_vars['whiteLine']+map_grid_vars['start2land']+3*map_grid_vars['zone_short'])
	land_grid_y = map_grid_vars['wall']+map_grid_vars['land_long']+map_grid_vars['whiteLine']+map_grid_vars['bot_width']
	land_grid = (land_grid_x, land_grid_y)
	land_real = (float(land_grid_x)/res,float(land_grid_y)/res)
	waypoints['land'] = (land_grid,land_real, 0)	#midpoint of land locations

	#calculate x and y for sea
	sea_grid_x = map_grid_vars['wall']+map_grid_vars['sea_long']+map_grid_vars['whiteLine']+map_grid_vars['bot_width']
	sea_grid_y = int(map_grid_vars['wall']+map_grid_vars['startH']+4.5*map_grid_vars['whiteLine']+map_grid_vars['Start2Sea']+3*map_grid_vars['zone_short'])
	sea_grid = (sea_grid_x, sea_grid_y)
	sea_real = (float(sea_grid_x)/res, float(sea_grid_y)/res)
	waypoints['sea'] = (sea_grid,sea_real, 0)	#midpoint of sea locations

	#calculate x and y values for air
	air_grid_x = map_grid_vars['air_long']+map_grid_vars['whiteLine']+map_grid_vars['bot_width']
	air_grid_y = int(map_grid_vars['height']-map_grid_vars['upPlt_2_Air']-1.5*map_grid_vars['whiteLine']-map_grid_vars['zone_short'])
	air_grid = (air_grid_x, air_grid_y)
	air_real = (float(air_grid_x)/res, float(air_grid_y)/res)
	waypoints['air'] = (air_grid, air_real, 0)	#midpoint of air locations

	#calculate x and y values for storage	
	stor_grid_x = int(map_grid_vars['wall']+map_grid_vars['edge2storage']+7.5*map_grid_vars['whiteLine']+7*map_grid_vars['zone_short'])
	stor_grid_y = map_grid_vars['height']-map_grid_vars['upPltH']-map_grid_vars['wall']-map_grid_vars['stor_long']-map_grid_vars['whiteLine']-map_grid_vars['bot_width']
	stor_grid = (stor_grid_x, stor_grid_y)
	stor_real = (float(stor_grid_x)/res, float(stor_grid_y)/res)
	waypoints['storage'] = (stor_grid, stor_real, 0)#midpoint of storage locations

	#calculate x and y values for start
	start_grid_x =  int(map_grid_vars['wall']+map_grid_vars['startW']/2)
	start_grid_y = int(map_grid_vars['wall']+map_grid_vars['startH']/2)	
	start_grid = (start_grid_x, start_grid_y)
	start_real = (float(start_grid_x)/res, float(start_grid_y)/res)
	waypoints['start'] = (start_grid,start_real)	#center of start location

	#calc x and y for waypoint in front of lower ramp on ground level
	grnd2ramp_grid_x = int(map_grid_vars['width']-map_grid_vars['loRmpW']/2)
	grnd2ramp_grid_y = int((map_grid_vars['height']-map_grid_vars['loPltH']-map_grid_vars['loRmpH'])/2)
	grnd2ramp_grid = (grnd2ramp_grid_x, grnd2ramp_grid_y)
	grnd2ramp_real = (float(grnd2ramp_grid_x)/res, float(grnd2ramp_grid_y)/res)
	waypoints['grnd2ramp'] = (grnd2ramp_grid, grnd2ramp_real, 0)

	#calc x and y for waypoint at center of lower platform
	lwrPlt_grid_x = int(map_grid_vars['width'] - map_grid_vars['loPltW']/2)
	lwrPlt_grid_y = int(map_grid_vars['height'] - map_grid_vars['loPltH']/2)
	lwrPlt_grid = (lwrPlt_grid_x, lwrPlt_grid_y)
	lwrPlt_real = (float(lwrPlt_grid_x)/res, float(lwrPlt_grid_y)/res)
	waypoints['lwrPlt'] = (lwrPlt_grid, lwrPlt_real,0)

	#print(waypoints)

	#arrays for loop that calcs x positions of individual storage locations
	xstor_grid = np.zeros((1,14), dtype = np.uint16)	
	xstor_real = np.zeros((1,14), dtype = np.float16)
	# calc the x position of the 1st storage location (closest to lower ramp)
	St01_grid_x = int(map_grid_vars['width'] - map_grid_vars['loRmpW']-map_grid_vars['edge2storage']-map_grid_vars['whiteLine']-map_grid_vars['zone_short']/2)
	for x in range(0,14):	#calc each x coord for remaining storage locations
		xstor_grid[0][x] = St01_grid_x - x*(map_grid_vars['zone_short']+map_grid_vars['whiteLine'])
		xstor_real[0][x] = float(St01_grid_x - x*(map_grid_vars['zone_short']+map_grid_vars['whiteLine']))/16

	St_grid_y = int(map_grid_vars['height'] - map_grid_vars['upPltH'] - map_grid_vars['wall'] - map_grid_vars['stor_long']/2)
	St_real_y = float(St_grid_y)/res
	
	#centers of storage locations
	waypoints['St01'] = ((xstor_grid[0][0],St_grid_y),(xstor_real[0][0],St_real_y),0)			
	waypoints['St02'] = ((xstor_grid[0][1],St_grid_y),(xstor_real[0][1],St_real_y),0)		
	waypoints['St03'] = ((xstor_grid[0][2],St_grid_y),(xstor_real[0][2],St_real_y),0)		
	waypoints['St04'] = ((xstor_grid[0][3],St_grid_y),(xstor_real[0][3],St_real_y),0)		
	waypoints['St05'] = ((xstor_grid[0][4],St_grid_y),(xstor_real[0][4],St_real_y),0)		
	waypoints['St06'] = ((xstor_grid[0][5],St_grid_y),(xstor_real[0][5],St_real_y),0)		
	waypoints['St07'] = ((xstor_grid[0][6],St_grid_y),(xstor_real[0][6],St_real_y),0)		
	waypoints['St08'] = ((xstor_grid[0][7],St_grid_y),(xstor_real[0][7],St_real_y),0)		
	waypoints['St09'] = ((xstor_grid[0][8],St_grid_y),(xstor_real[0][8],St_real_y),0)		
	waypoints['St10'] = ((xstor_grid[0][9],St_grid_y),(xstor_real[0][9],St_real_y),0)		
	waypoints['St11'] = ((xstor_grid[0][10],St_grid_y),(xstor_real[0][10],St_real_y),0)		
	waypoints['St12'] = ((xstor_grid[0][11],St_grid_y),(xstor_real[0][11],St_real_y),0)		
	waypoints['St13'] = ((xstor_grid[0][12],St_grid_y),(xstor_real[0][12],St_real_y),0)		
	waypoints['St14'] = ((xstor_grid[0][13],St_grid_y),(xstor_real[0][13],St_real_y),0)	
	
	#center of air locations
	air_grid_x = int(map_grid_vars['air_long']/2)
	air_real_x = float(air_grid_x)/res
	A01_grid_y = int(map_grid_vars['height']-map_grid_vars['upPlt_2_Air']-map_grid_vars['whiteLine']-map_grid_vars['zone_short']/2)
	A02_grid_y = int(map_grid_vars['height']-map_grid_vars['upPlt_2_Air']-2*map_grid_vars['whiteLine']-1.5*map_grid_vars['zone_short'])
	waypoints['A01'] = ((air_grid_x, A01_grid_y),(float(air_grid_x)/res, float(A01_grid_y)/res),0)		
	waypoints['A02'] = ((air_grid_x, A02_grid_y),(float(air_grid_x)/res, float(A02_grid_y)/res),0)

	#center of land locations
	xland_grid = np.zeros((1,6), dtype = np.uint16)	
	xland_real = np.zeros((1,6), dtype = np.float16)	
	L01_grid_x = int(map_grid_vars['width'] - map_grid_vars['wall'] - map_grid_vars['start2land'] - map_grid_vars['whiteLine'] - map_grid_vars['zone_short']/2)	#loc of 1st land zone
	for x in range(0,6):	#calc each x coord for remaining land locations
			xland_grid[0][x] = L01_grid_x - x*(map_grid_vars['zone_short']+map_grid_vars['whiteLine'])
			xland_real[0][x] = float(L01_grid_x - x*(map_grid_vars['zone_short']+map_grid_vars['whiteLine']))/res

	L_grid_y = int(map_grid_vars['wall']+map_grid_vars['land_long']/2)
	L_real_y = float(L_grid_y)/res
	waypoints['L06'] = ((xland_grid[0][0],L_grid_y),(xland_real[0][0],L_real_y),0)
	waypoints['L05'] = ((xland_grid[0][1],L_grid_y),(xland_real[0][1],L_real_y),0)
	waypoints['L04'] = ((xland_grid[0][2],L_grid_y),(xland_real[0][2],L_real_y),0)
	waypoints['L03'] = ((xland_grid[0][3],L_grid_y),(xland_real[0][3],L_real_y),0)
	waypoints['L02'] = ((xland_grid[0][4],L_grid_y),(xland_real[0][4],L_real_y),0)
	waypoints['L01'] = ((xland_grid[0][5],L_grid_y),(xland_real[0][5],L_real_y),0)

	#center of sea locations
	ysea_grid = np.zeros((1,6), dtype = np.uint16)	
	ysea_real = np.zeros((1,6), dtype = np.float16)
	Se01_grid_y = int(map_grid_vars['height']-map_grid_vars['upPltH']-map_grid_vars['wall']-map_grid_vars['EdgetoSea']-map_grid_vars['whiteLine']-map_grid_vars['zone_short']/2)	#loc of 1st sea zone
	for x in range(0,6):	#calc each x coord for remaining sea locations
			ysea_grid[0][x] = Se01_grid_y - x * (map_grid_vars['zone_short'] + map_grid_vars['whiteLine'])
			ysea_real[0][x] = float(Se01_grid_y - x * (map_grid_vars['zone_short'] + map_grid_vars['whiteLine']))/res
	Sea_grid_x = int(map_grid_vars['wall']+map_grid_vars['sea_long']/2)
	waypoints['Se01'] = ((Sea_grid_x,ysea_grid[0][0]),(float(Sea_grid_x)/res, ysea_real[0][0]),0)
	waypoints['Se02'] = ((Sea_grid_x,ysea_grid[0][1]),(float(Sea_grid_x)/res, ysea_real[0][1]),0)
	waypoints['Se03'] = ((Sea_grid_x,ysea_grid[0][2]),(float(Sea_grid_x)/res, ysea_real[0][2]),0)
	waypoints['Se04'] = ((Sea_grid_x,ysea_grid[0][3]),(float(Sea_grid_x)/res, ysea_real[0][3]),0)
	waypoints['Se05'] = ((Sea_grid_x,ysea_grid[0][4]),(float(Sea_grid_x)/res, ysea_real[0][4]),0)
	waypoints['Se06'] = ((Sea_grid_x,ysea_grid[0][5]),(float(Sea_grid_x)/res, ysea_real[0][5]),0)
	
	return(waypoints)


