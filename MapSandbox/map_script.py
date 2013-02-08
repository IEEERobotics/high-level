"""
Ricker Snow
this is a short script that makes the map by calling the mk_map() function from CV_Map.py and then outputs the Map to 5 text files via map2txt() from map2txt.py. Each text file is a layer (description, status, color, level, and path).  See CV_Map.py for details about each layer.
"""

import CV_Map
import map2txt

def main():
	
	#print("main1")

	#Make map
	Map = CV_Map.mk_map()
	#output map to text
	map2txt.map2txt(Map)

	#print("main2")
	return 0

if __name__ == "__main__":
	main()
