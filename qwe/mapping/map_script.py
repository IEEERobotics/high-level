"""
Ricker Snow
this is a short script that makes the map by calling the mk_map() function from CV_Map.py, flips the map, makes the waypoints, and pickles the map and waypoints.  map2txt can also be called to make text files of the map to verify the map visually. 
"""
import argparse
import CV_Map
from map_class import MapClass
import map2txt
import flip_map
import pickler
import mk_waypoints

def main():
	
  	parser = argparse.ArgumentParser(description='Map generator')
	parser.add_argument('-r', '--res', help='Map resolution', type=int, default='16' )
  	args = parser.parse_args()	#args.res has units inches/tile
	
	#print(args.res)
	"""
	Make dictonaries of variables that need, or may need, to be passed to another function
	"""
	map_real_vars = {}	#raw map variables with units inches
	map_prop_vars= {}	#descriptive map variables used in mk_map() that may need to be passed to vision or localization process 

	map_real_vars['height'] = 73	#Upper platform width
	map_real_vars['width'] = 97	#width of entire course
	map_real_vars['upPltW'] = 24	#Upper platform width
	map_real_vars['upPltH'] = 24	#Upper platform height
	map_real_vars['upRmpW'] = 49	#upper ramp width
	map_real_vars['upRmpH'] = 24	#upper ramp height
	map_real_vars['loPltW'] = 24	#lower platform width
	map_real_vars['loPltH'] = 24	#lower platform height
	map_real_vars['loRmpW'] = 24	#lower ramp width
	map_real_vars['loRmpH'] = 24	#lower ramp height
	map_real_vars['wall'] = 0.75 	#wall thickness
	map_real_vars['whiteLine'] = 0.5	#thickness of white lines
	map_real_vars['startW'] = 12	#start square width
	map_real_vars['startH'] = 12	#start square height
	map_real_vars['upPlt_2_Air'] = 8.75	
	map_real_vars['zone_short'] = 2.5	#the short dimension of each individual loading slot
	map_real_vars['air_long'] = 3	#the long dimension of each individual loading slot
	map_real_vars['sea_long'] = 4
	map_real_vars['land_long'] = 5		
	map_real_vars['stor_long'] = 6	
	map_real_vars['EdgetoSea'] = 8.5  #from edge of upper platform to start of sea area
	map_real_vars['Start2Sea'] = 8.5
	map_real_vars['edge2storage'] = 14.875
	map_real_vars['start2land'] = 31.75 #distance b/w start and land
	map_real_vars['cargoL'] = 42.5
	map_real_vars['seaH'] = 18.5
	map_real_vars['landW'] = 18.5
	map_real_vars['bot_width'] = 12		
	map_real_vars['bot_length'] = 12

	#map property variables
	#status vars
	map_prop_vars['filled'] = 0
	map_prop_vars['empty'] = 1
	#color vars
	map_prop_vars['unk'] = 0
	map_prop_vars['blue'] = 1
	map_prop_vars['black'] = 2
	map_prop_vars['green'] = 3
	map_prop_vars['yellow'] = 4
	map_prop_vars['red'] = 5
	map_prop_vars['brown'] = 6
	map_prop_vars['white'] = 7
	#level vars
	map_prop_vars['ground'] = 0
	map_prop_vars['ramp'] = 1
	map_prop_vars['lwr_plat'] = 2
	map_prop_vars['upp_plat'] = 3
	#path vars
	map_prop_vars['path'] = 0
	map_prop_vars['not_path'] = 1
	#desc variables
	map_prop_vars['driv_srfc'] = 0
	map_prop_vars['start'] = 1
	map_prop_vars['storage'] = 2
	map_prop_vars['land'] = 3
	map_prop_vars['sea'] = 4
	map_prop_vars['air'] = 5
	map_prop_vars['line'] = 7
	map_prop_vars['wall'] = 8
	map_prop_vars['edge'] = 9

	map_grid_vars = map_real_vars.copy()	#map variables that will have units 'tiles'
	for key in map_grid_vars:		#multiply all of the variables by the resolution to get units of 'tiles'
		map_grid_vars[key] = int(args.res * map_grid_vars[key])
	
	#print(map_grid_vars);

	#Make map
	Map = CV_Map.mk_map(args.res, map_grid_vars, map_prop_vars)
	#Flip the map
	Map = flip_map.flip_map(Map)
	#Make the waypoints
	waypoints = mk_waypoints.mk_waypoints(args.res, map_grid_vars)
	#Output map to text
	map2txt.map2txt(Map)
	#pickle the map
	pickler.pickle_map(Map)
	#pickle the waypoints
	pickler.pickle_waypoints(waypoints)
	#pickle the map_prop_vars
	pickler.pickle_map_prop_vars(map_prop_vars)
	#unpickle the waypoints - to test function
	#Map_result = pickler.unpickle_map('map.pkl')
	#unpickle the waypoints - to test function
	#waypoints_result = pickler.unpickle_waypoints('waypoints.pkl')
	#unpickle the map_prop_vars - to test function
	#map_prop_vars_result = pickler.unpickle_map_prop_vars('map_prop_vars.pkl')

	#print(Map_result.grid[0][0]['desc'])
	#print(waypoints_result['land'])
	#print(map_prop_vars_result['blue'])

	return 0

if __name__ == "__main__":
	main()
