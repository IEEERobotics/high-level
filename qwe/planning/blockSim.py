import Block;

class BlockSim:
	
	def process(self, loc, count):
		listofBlocks = []
		
		filename = "./planning/" + str(loc) + ".txt"
		f = open(filename, 'r')
		data = f.read()
		#print line
		lines = data.split('\n')
		#print len(lines)

		for i in range(len(lines)):
			items = lines[i].split()
			blk = Block.Block()
			blk.setColor(items[0])
			blk.setSize(items[1])
			blk.setLocation(items[2],items[3])

			#print blk.getColor(), blk.getSize(), blk.getLocation()
			listofBlocks.append(blk)

		return listofBlocks[count]


#bs = BlockSim()
#b = bs.process(2)
#print b.getColor(), b.getSize(), b.getLocation()
