import mk_map_test
import map2txt

def main():
	print("main1")
	Map = mk_map_test.mk_map_test()
	map2txt.map2txt(Map)
	print("main2")
	return 0

if __name__ == "__main__":
	main()
