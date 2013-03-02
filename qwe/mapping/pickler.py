"""
The pickler contains pickling and unpickling functions for the map and waypoints data structures. 

"""
import pickle

"""
pickle_map accepts the map as input and pickles the map to a file map.pkl.  Nothing is returned.
"""
def pickle_map(Map):

	#pickle map
	output = open('map.pkl', 'w')
	pickle.dump(Map, output)
	output.close()
	
	return()

"""
pickle_waypoints accepts the waypoints as input and pickles the waypoints to a file waypoints.pkl.  Nothing is returned.
"""
def pickle_waypoints(waypoints):

	#pickle map
	output = open('waypoints.pkl', 'w')
	pickle.dump(waypoints, output)
	output.close()
	
	return()


"""
unpickle_map takes no arguments. It unpickles the map data structure and returns it.  
"""
def unpickle_map():

	pkl_file = open('map.pkl', 'r')
	Map = pickle.load(pkl_file)
	pkl_file.close()

	return(Map)

"""
unpickle_waypoints takes no arguments.  It unpickles the waypoints data structure and returns it.
"""
def unpickle_waypoints():

	pkl_file = open('waypoints.pkl', 'r')
	waypoints = pickle.load(pkl_file)
	pkl_file.close()

	return(waypoints)

"""
pickle_map_prop_vars accepts the map_prop_vars dict which may be useful for any process that acceses the map.  Nothing is returned.
"""
def pickle_map_prop_vars(map_prop_vars):
	output = open('map_prop_vars.pkl', 'w')
	pickle.dump(map_prop_vars, output)
	output.close()
	return()

"""
unpickle_map_prop_vars accepts no arguments.  The map_prop_vars dict is returned.
"""
def unpickle_map_prop_vars():
	pkl_file = open('map_prop_vars.pkl', 'r')
	map_prop_vars = pickle.load(pkl_file)
	pkl_file.close()
	return(map_prop_vars)
