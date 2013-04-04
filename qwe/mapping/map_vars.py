"""
Make dictonaries of variables that need, or may need, to be passed to another function
"""
map_real_vars = {}	#raw map variables with units inches
map_prop_vars= {}	#descriptive map variables used in mk_map() that may need to be passed to vision or localization process 

map_real_vars['height'] = 73	#height of entire course
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
map_real_vars['EdgetoSea'] = 8.25  #from edge of upper platform to start of sea area
map_real_vars['Start2Sea'] = 8.25
map_real_vars['edge2storage'] = 14.875
map_real_vars['start2land'] = 32.25 #distance b/w start and land
map_real_vars['cargoL'] = 42.5
map_real_vars['seaH'] = 18.5
map_real_vars['landW'] = 18.5
map_real_vars['bot_width'] = 12		
map_real_vars['bot_length'] = 12
map_real_vars['offset'] = 5
map_real_vars['start_x'] = 4
map_real_vars['start_y'] = 7.75

#map property variables
#status vars
map_prop_vars['filled'] = 'a'
map_prop_vars['empty'] = 'b'
#color vars
map_prop_vars['unk'] = 'c'
map_prop_vars['blue'] = 'd'
map_prop_vars['black'] = 'e'
map_prop_vars['green'] = 'f'
map_prop_vars['yellow'] = 'g'
map_prop_vars['red'] = 'h'
map_prop_vars['brown'] = 'i'
map_prop_vars['white'] = 'j'
#level vars
map_prop_vars['ground'] = 'k'
map_prop_vars['ramp'] = 'l'
map_prop_vars['lwr_plat'] = 'm'
map_prop_vars['upp_plat'] = 'n'
#path vars
map_prop_vars['path'] = 'o'
map_prop_vars['not_path'] = 'p'
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

#print(map_grid_vars);
