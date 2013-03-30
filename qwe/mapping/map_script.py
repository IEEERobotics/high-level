#!/usr/bin/env python

"""
Ricker Snow
this is a short script that makes the map by calling the mk_map() function from CV_Map.py, flips the map, makes the waypoints, and pickles the map and waypoints.  map2txt can also be called to make text files of the map to verify the map visually. 
"""
import argparse
import CV_Map
import map_vars as mvars
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

	map_grid_vars = mvars.map_real_vars.copy()	#map variables that will have units 'tiles'
	for key in map_grid_vars:		#multiply all of the variables by the resolution to get units of 'tiles'
		map_grid_vars[key] = int(args.res * map_grid_vars[key])

	#Make map
	Map = CV_Map.mk_map(args.res, map_grid_vars, mvars.map_prop_vars)
	#Output map to text - the function map2txt flips the map during storing so don't need to call flip map first
	map2txt.map2txt(Map)
	#Flip the map
	Map = flip_map.flip_map(Map)
	#Make the waypoints
	waypoints = mk_waypoints.mk_waypoints(args.res, map_grid_vars)
	#pickle the map
	pickler.pickle_map(Map)
	#pickle the waypoints
	pickler.pickle_waypoints(waypoints)
	#pickle the map_prop_vars
	pickler.pickle_map_prop_vars(mvars.map_prop_vars)
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
