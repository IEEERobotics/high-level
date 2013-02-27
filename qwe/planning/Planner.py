"""
Code for python planner
"""

import blockSim as BlockDet
import twoWayDict as twd

class Planner:
	nextSeaLandBlock = []
	nextAirBlock = []
	armList = []
	
	nextSeaBlockLoc = []
	nextLandBlockLoc = []
	nextAirBlockLoc = []
	
	nsbl = twd.TwoWayDict()
	nlbl = twd.TwoWayDict()
	
	#get current location
	def getCurrentLocation(self):
		return "CurrentLoc"

	#more to the next block - use this if next block location is
	#handled by nav instead of planner
	def moveToNextBlock(self):
		print "Moving to Next Block"
		self.moveTo(self.getCurrentLocation(), "nextblock loc")
	
	#move from start to end
	def moveTo(self, startLoc, endLoc):
		print "Moving from ", startLoc, " to ", endLoc

	
	# Scan the given location for the first time
	# use this if scanning first then dropping blocks
	def scanFirstTime(self, loc):
		print "Scanning Storage"		
		print "Initiating Storage Scan"
		print "updating list of sea, land and air blocks"
			
		count = 0
		if loc == "storage":
			count = 14
		else:
			count = 6

		#Scan all blocks in area
		for i in range(count):
			#replace blocksim with block detector code
			bs = BlockDet.BlockSim()
			block = bs.process(loc,i)
			## possibly update block location here
			## block.setLocation(self.getCurrentLocation());
			print "scanning block", i+1, ":", block.getColor(), block.getSize(), block.getLocation()
			
			if loc == "storage":
				if block.getSize() == "small":
					self.nextAirBlock.append(block)
				else:
					self.nextSeaLandBlock.append(block)
			elif loc == "land":
				self.nextLandBlockLoc.append(block)
			elif loc == "sea":
				self.nextSeaBlockLoc.append(block)
			# Update target location for next block

			nextLoc = block.getLocation();
			bLoc = [int(nextLoc[0]), int(nextLoc[1])]
			bLoc[1] = bLoc[1] + 2; # change 2 to appropriate value
				
			self.moveTo(self.getCurrentLocation(), bLoc)
		#end for

		#print self.nextAirBlock
		#print self.nextSeaLandBlock

	#end scanFirstTime

	# use this if dropping off blocks during scan
	def scanStorageFirstTime(self, loc):
		print "--Scanning Storage"
		print "--Initiating Storage Scan"
		print "--updating list of sea, land and air blocks"
				
		#Scan all 14 blocks in storage area
		for i in range(14):
			#replace blocksim with block detector code
			bs = BlockDet.BlockSim()
			block = bs.process(loc,i)
			## possibly update block location here
			## block.setLocation(self.getCurrentLocation());
			print "---scanning block", i+1, ":", block.getColor(), block.getSize(), block.getLocation()
			
			if block.getSize() == "small":
				self.nextAirBlock.append(block)
			else:
				self.nextSeaLandBlock.append(block)
			
			# Update target location for next block
			
			nextLoc = block.getLocation();
			bLoc = [int(nextLoc[0]), int(nextLoc[1])]
			bLoc[1] = bLoc[1] + 2; # change 2 to appropriate value
			
			self.moveTo(self.getCurrentLocation(), bLoc)
	#end for
	
	#print self.nextAirBlock
	#print self.nextSeaLandBlock
	
	#end scanStorageFirstTime

	# use this if dropping off blocks during scan
	def scanLandorSeaFirstTime(self, loc):
		print "Initiating", loc, "scan"
		print "updating", loc, "block locations"
			
		for i in range(6):
			print "scanning", loc, "block location", i+1

			bs = BlockDet.BlockSim()
			blockLoc = bs.process(loc,i)
			print "scanning block Location", i+1, ":", blockLoc.getColor(), blockLoc.getSize(), blockLoc.getLocation()
			
			if loc == "land":
				self.nextLandBlockLoc.append(blockLoc)
				self.nlbl[blockLoc.getColor()] = blockLoc.getLocation()
			elif loc == "sea":
				self.nextSeaBlockLoc.append(blockLoc)
				self.nsbl[blockLoc.getColor()] = blockLoc.getLocation()
			
			nextLoc = blockLoc.getLocation();
			bLoc = [int(nextLoc[0]), int(nextLoc[1])]
			bLoc[1] = bLoc[1] + 2; # change 2 to appropriate value
		
			self.moveTo(self.getCurrentLocation(), bLoc)
		#end if
	#end scanLandorSeaFirstTime


	def processSeaLand(self):
		if (not self.nextAirBlock and not self.nextSeaLandBlock):
			self.scanStorageFirstTime("storage")
			self.moveTo(self.getCurrentLocation(), "Storage Start")

		armCount = 0
		armList = []
		print "+++++ +++++ +++++ +++++ +++++ +++++"
		for i in range(len(self.nextSeaLandBlock)):
			block = self.nextSeaLandBlock[i];
			print "Processing: [", block.getColor(), block.getSize(), block.getLocation(), "]"
			self.pickUpBlock(block.getLocation())
			armList.append(block)
			armCount = armCount + 1;

			if armCount == 2:
				print "picked up 2 blocks"
				
				#Both arms contain sea blocks
				if armList[0].getSize() == "medium" and armList[1].getSize() == "medium":
					self.moveTo(self.getCurrentLocation(), "seaStart")
					if not self.nextSeaBlockLoc:
						self.scanLandorSeaFirstTime("sea")
					
					print "Arm 0 - [", armList[0].getColor(), armList[0].getLocation(), "] -- Location: ", self.nsbl[armList[0].getColor()]
					print "Arm 1 - [", armList[1].getColor(), armList[1].getLocation(), "] -- Location: ", self.nsbl[armList[1].getColor()]
					
					if self.nsbl[armList[0].getColor()] > self.nsbl[armList[1].getColor()]:
						self.placeBlock(armList[1], self.nsbl[armList[1].getColor()], "Arm - 1")
						self.placeBlock(armList[0], self.nsbl[armList[0].getColor()], "Arm - 0")
					else:
						print "arm 0 first"
						self.placeBlock(armList[0], self.nsbl[armList[0].getColor()], "Arm - 0")
						self.placeBlock(armList[1], self.nsbl[armList[1].getColor()], "Arm - 1")
					#place A and B in the closeness order (sea.ColorLoc)

				#Both arms contain land blocks
				elif armList[0].getSize() == "large" and armList[1].getSize() == "large":
					self.moveTo(self.getCurrentLocation(), "LandStart")
					if not self.nextLandBlockLoc:
						self.scanLandorSeaFirstTime("land")
			
					print "Arm 0 - [", armList[0].getColor(), armList[0].getLocation(), "] -- Location: ", self.nlbl[armList[0].getColor()]
					print "Arm 1 - [", armList[1].getColor(), armList[1].getLocation(), "] -- Location: ", self.nlbl[armList[1].getColor()]
		
					#MIGHT HAVE TO REVERSE For Land or for both Storage and Sea
					#- depends on how the map represents 0,0 and how distances increase
					if self.nlbl[armList[0].getColor()] > self.nlbl[armList[1].getColor()]:
						self.placeBlock(armList[1], self.nlbl[armList[1].getColor()], "Arm - 1")
						self.placeBlock(armList[0], self.nlbl[armList[0].getColor()], "Arm - 0")
					else:
						print "arm 0 first"
						self.placeBlock(armList[0], self.nlbl[armList[0].getColor()], "Arm - 0")
						self.placeBlock(armList[1], self.nlbl[armList[1].getColor()], "Arm - 1")

				
					#place A and B in the closeness order (land.ColorLoc)

				#One arm contains sea block and other contains land block
				elif armList[0].getSize() == "medium" and armList[1].getSize() == "large":
					self.moveTo(self.getCurrentLocation(), "seaStart")
					if not self.nextSeaBlockLoc:
						self.scanLandorSeaFirstTime("sea")
					print "Arm 0 - [", armList[0].getColor(), armList[0].getLocation(), "] -- Location: ", self.nsbl[armList[0].getColor()]
					self.placeBlock(armList[0], self.nsbl[armList[0].getColor()], "Arm - 0")

					self.moveTo(self.getCurrentLocation(), "landStart")
					if not self.nextLandBlockLoc:
						self.scanLandorSeaFirstTime("land")
					print "Arm 1 - [", armList[1].getColor(), armList[1].getLocation(), "] -- Location: ", self.nlbl[armList[1].getColor()]
					self.placeBlock(armList[1], self.nlbl[armList[1].getColor()], "Arm - 1")
						
				#One arm contains land block and other contains sea block
				elif armList[0].getSize() == "large" and armList[1].getSize() == "medium":
					# even if the orders are different, first go to sea then land
					self.moveTo(self.getCurrentLocation(), "SeaStart")
					if not self.nextSeaBlockLoc:
						self.scanLandorSeaFirstTime("sea")
					print "Arm 1 - [", armList[1].getColor(), armList[1].getLocation(), "] -- Location: ", self.nsbl[armList[1].getColor()]
					self.placeBlock(armList[1], self.nsbl[armList[1].getColor()], "Arm - 1")

					self.moveTo(self.getCurrentLocation(), "LandStart")
					if not self.nextLandBlockLoc:
						self.scanLandorSeaFirstTime("land")
					print "Arm 0 - [", armList[0].getColor(), armList[0].getLocation(), "] -- Location: ", self.nlbl[armList[0].getColor()]
					self.placeBlock(armList[0], self.nlbl[armList[0].getColor()], "Arm - 0")
								
				armCount = 0
				armList = []
				print "===== ===== ===== ===== ===== ===== ===== ===== ===== ====="
				self.moveTo(self.getCurrentLocation(), "storageStart")
			#end if
		#end for
	#end processSeaLand
				
	def processAir(self):
		for i in range(len(self.nextAirBlock)):
			block = self.nextAirBlock[i];
			print "Processing: [", block.getColor(), block.getSize(), block.getLocation(), "]"
			self.pickUpBlock(block.getLocation());
		#end for
		
		print "Move to Ramp, up the ramp, to the drop-off"
		print "Scan air drop-off"
		print "Drop Air Blocks"

	def pickUpBlock(self, blockLoc):
		self.moveTo(self.getCurrentLocation(), blockLoc);
		print "Picking Up Block at ", blockLoc
		#print "decide which arm is free"
		#print "move free arm to pick up block"
		#print "mark map loc corresponding to blockLoc as empty"
					
		#print "if no arm is free, return error"


	def placeBlock(self, block, blockLoc, arm):
		self.moveTo(self.getCurrentLocation(), blockLoc)
		print "Placing block from ", arm, "at", blockLoc

		#print "find locations (x,y) of both blocks held by the bot"
		#print "stop at nearest (x,y)"
		#print "update blockLoc list to remove the 2 (x,y)s or mark them visited"
	
	
	def start(self):
		print "Move to Storage Start"
		self.moveTo(self.getCurrentLocation(), "storageStart")
		print "Scan Storage"
		self.scanStorageFirstTime("storage") # BUG: This should not be hardcoded. Currently fails.
		print "Move to Storage Start"
		self.moveTo(self.getCurrentLocation(), "storageStart")
		print "***********************************************"
		print "********** Processing - Sea and Land **********"
		print "***********************************************"
		self.processSeaLand()
		print "**************************************"
		print "********** Processing - Air **********"
		print "**************************************"
		self.processAir()

def run(bot_loc, blocks, zones, corners, waypoints):
  # TODO Handle shared data, start your process from here
  plan = Planner()
  plan.start()
  
if __name__ == "__main__":
  plan = Planner()
  plan.start()
