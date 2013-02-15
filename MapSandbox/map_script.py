"""
Ricker Snow
this is a short script that makes the map by calling the mk_map() function from CV_Map.py and then outputs the Map to 5 text files via map2txt() from map2txt.py. Each text file is a layer (description, status, color, level, and path).  See CV_Map.py for details about each layer.
"""
import argparse
import CV_Map
import map2txt

def main():
	
  	parser = argparse.ArgumentParser(description='Map generator')
	parser.add_argument('-r', '--res', help='Map resolution', type=int, default='16' )
  	args = parser.parse_args()
	
	print(args.res)

	#Make map
	Map = CV_Map.mk_map(args.res)
	#output map to text
	map2txt.map2txt(Map)
	#txt2map.txt2map(res)
	#print("main2")
	return 0

if __name__ == "__main__":
	main()
