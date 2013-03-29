"""
Code for python planner
"""

import blockSim as BlockDet
import twoWayDict as twd

class Planner:
  nextSeaLandBlock = [] #list of the next available sea or land block to pick up
  nextAirBlock = [] #list of the 2 air blocks in storage
  armList = [] #list of which arm contains what
  armID = [2,0]	# armID[0] = right arm, armID[1] = left arm
    
  nextSeaBlockLoc = []
  nextLandBlockLoc = []
  nextAirBlockLoc = []
  
  nsbl = twd.TwoWayDict()
  nlbl = twd.TwoWayDict()
  
  
  def __init__(self, bot_loc, blobs, blocks, zones, waypoints, scPlanner, bot_state, qMove_nav):
    """Setup navigation class

    :param bot_loc: Shared dict updated with best-guess location of bot by localizer
    :param blocks: list of blocks
    :param zones: 
    :param waypoints: Multiprocessing.Queue object for passing movement feedback to localizer from navigator
    :param si: Serial interface object for sending commands to low-level boards
    :param bot_state: Dict of information about the current state of the bot (ex macro/micro nav)
    :param qMove_nav: Multiprocessing.Queue object for passing movement commands to navigation (mostly from Planner)
    """    
    # Store passed-in data
    self.bot_loc = bot_loc
    self.blobs = blobs
    self.blocks = blocks
    self.zones = zones
    self.waypoints = waypoints
    self.scPlanner = scPlanner
    self.bot_state = bot_state
    self.qMove_nav = qMove_nav
    
    self.armID[0] = self.scPlanner.right_arm 
    self.armID[0] = self.scPlanner.left_arm
  
  #get current location
  def getCurrentLocation(self):
    #print self.bot_loc
    return self.bot_loc

  #more to the next block - use this if next block location is
  #handled by nav instead of planner
  def moveToNextBlock(self):
    print "Moving to Next Block"
    self.moveTo(self.getCurrentLocation(), "nextblock loc")
  
  #move from start to end
  def moveToWayPoint(self, startLoc, endLoc):
    print "Moving from ", startLoc, " to ", endLoc, "--", self.waypoints[endLoc]

  def moveTo(Self, startLoc, endLoc):
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
      self.moveToWayPoint(self.getCurrentLocation(), "storage")

    armCount = 0
    armList = []
    print "+++++ +++++ +++++ +++++ +++++ +++++"
    for i in range(len(self.nextSeaLandBlock)):
      block = self.nextSeaLandBlock[i];
      print "Processing: [", block.getColor(), block.getSize(), block.getLocation(), "]"
      self.pickUpBlock(block.getLocation(), armCount) #arm 0 or 1.
      armList.append(block)
      armCount = armCount + 1;

      if armCount == 2:
        print "picked up 2 blocks"
        
        #Both arms contain sea blocks
        if armList[0].getSize() == "medium" and armList[1].getSize() == "medium":
          self.moveToWayPoint(self.getCurrentLocation(), "sea")
          if not self.nextSeaBlockLoc:
            self.scanLandorSeaFirstTime("sea")
          
          print "Arm 0 - [", armList[0].getColor(), armList[0].getLocation(), "] -- Location: ", self.nsbl[armList[0].getColor()]
          print "Arm 1 - [", armList[1].getColor(), armList[1].getLocation(), "] -- Location: ", self.nsbl[armList[1].getColor()]
          
          if self.nsbl[armList[0].getColor()] > self.nsbl[armList[1].getColor()]:
            self.placeBlock(armList[1], self.nsbl[armList[1].getColor()], 1)
            self.placeBlock(armList[0], self.nsbl[armList[0].getColor()], 0)
          else:
            print "arm 0 first"
            self.placeBlock(armList[0], self.nsbl[armList[0].getColor()], 0)
            self.placeBlock(armList[1], self.nsbl[armList[1].getColor()], 1)
          #place A and B in the closeness order (sea.ColorLoc)

        #Both arms contain land blocks
        elif armList[0].getSize() == "large" and armList[1].getSize() == "large":
          self.moveToWayPoint(self.getCurrentLocation(), "land")
          if not self.nextLandBlockLoc:
            self.scanLandorSeaFirstTime("land")
      
          print "Arm 0 - [", armList[0].getColor(), armList[0].getLocation(), "] -- Location: ", self.nlbl[armList[0].getColor()]
          print "Arm 1 - [", armList[1].getColor(), armList[1].getLocation(), "] -- Location: ", self.nlbl[armList[1].getColor()]
    
          #MIGHT HAVE TO REVERSE For Land or for both Storage and Sea
          #- depends on how the map represents 0,0 and how distances increase
          if self.nlbl[armList[0].getColor()] > self.nlbl[armList[1].getColor()]:
            self.placeBlock(armList[1], self.nlbl[armList[1].getColor()], 1)
            self.placeBlock(armList[0], self.nlbl[armList[0].getColor()], 0)
          else:
            print "arm 0 first"
            self.placeBlock(armList[0], self.nlbl[armList[0].getColor()], 0)
            self.placeBlock(armList[1], self.nlbl[armList[1].getColor()], 1)
        
        #place A and B in the closeness order (land.ColorLoc)

        #One arm contains sea block and other contains land block
        elif armList[0].getSize() == "medium" and armList[1].getSize() == "large":
          self.moveToWayPoint(self.getCurrentLocation(), "sea")
          if not self.nextSeaBlockLoc:
            self.scanLandorSeaFirstTime("sea")
          print "Arm 0 - [", armList[0].getColor(), armList[0].getLocation(), "] -- Location: ", self.nsbl[armList[0].getColor()]
          self.placeBlock(armList[0], self.nsbl[armList[0].getColor()], 0)

          self.moveToWayPoint(self.getCurrentLocation(), "land")
          if not self.nextLandBlockLoc:
            self.scanLandorSeaFirstTime("land")
          print "Arm 1 - [", armList[1].getColor(), armList[1].getLocation(), "] -- Location: ", self.nlbl[armList[1].getColor()]
          self.placeBlock(armList[1], self.nlbl[armList[1].getColor()], 1)
            
        #One arm contains land block and other contains sea block
        elif armList[0].getSize() == "large" and armList[1].getSize() == "medium":
          # even if the orders are different, first go to sea then land
          self.moveToWayPoint(self.getCurrentLocation(), "sea")
          if not self.nextSeaBlockLoc:
            self.scanLandorSeaFirstTime("sea")
          print "Arm 1 - [", armList[1].getColor(), armList[1].getLocation(), "] -- Location: ", self.nsbl[armList[1].getColor()]
          self.placeBlock(armList[1], self.nsbl[armList[1].getColor()], 1)

          self.moveToWayPoint(self.getCurrentLocation(), "land")
          if not self.nextLandBlockLoc:
            self.scanLandorSeaFirstTime("land")
          print "Arm 0 - [", armList[0].getColor(), armList[0].getLocation(), "] -- Location: ", self.nlbl[armList[0].getColor()]
          self.placeBlock(armList[0], self.nlbl[armList[0].getColor()], 0)
                
        armCount = 0
        armList = []
        print "===== ===== ===== ===== ===== ===== ===== ===== ===== ====="
        self.moveToWayPoint(self.getCurrentLocation(), "storage")
      #end if
    #end for
  #end processSeaLand
        
  def processAir(self):
    for i in range(len(self.nextAirBlock)):
      block = self.nextAirBlock[i];
      print "Processing: [", block.getColor(), block.getSize(), block.getLocation(), "]"
      self.pickUpBlock(block.getLocation(), i);
    #end for
    
    print "Move to Ramp, up the ramp, to the drop-off"
    self.moveToWayPoint(self.getCurrentLocation(), "grnd2ramp") #normal speed
    self.moveToWayPoint(self.getCurrentLocation(), "lwrPlt") #ramp speed
    #self.moveToWayPint(self.getCurrentLocation(), "uprRamp") #normal speed
    self.moveToWayPoint(self.getCurrentLocation(), "air") #ramp speed
          
    print "Scan air drop-off"
    print "Drop Air Blocks"


  def pickUpBlock(self, blockLoc, arm):
    armId = self.armID[arm]
    
    self.moveTo(self.getCurrentLocation(), blockLoc)
    print "Picking Up Block at ", blockLoc, "with Arm", armId
    
    self.scPlanner.gripperOpen(armId)
    self.scPlanner.armDown(armId)
    self.scPlanner.gripperClose(armId)
    self.scPlanner.armUp(armId)
    
  def placeBlock(self, block, blockLoc, arm):
    armId = self.armID[arm]
          
    self.moveTo(self.getCurrentLocation(), blockLoc)
    print "Placing block from ", self.armID[arm], "at", blockLoc
    
    self.scPlanner.armDown(armId)
    self.scPlanner.gripperOpen(armId)
    self.scPlanner.armUp(armId)
    self.scPlanner.gripperClose(armId)

    
  def test(self):
  	print self.waypoints
  	print len(self.waypoints)
  	print self.waypoints["storage"]
  
  def start(self):
    print "Move to Storage Start"
    self.moveToWayPoint(self.getCurrentLocation(), "storage")
    print "Scan Storage"
    self.scanStorageFirstTime("storage") # BUG: This should not be hardcoded. Currently fails.
    print "Move to Storage Start"
    self.moveToWayPoint(self.getCurrentLocation(), "storage")
    print "***********************************************"
    print "********** Processing - Sea and Land **********"
    print "***********************************************"
    self.processSeaLand()
    print "**************************************"
    print "********** Processing - Air **********"
    print "**************************************"
    self.processAir()

def run(bot_loc, blobs, blocks, zones, waypoints, scPlanner, bot_state, qMove_nav):
  # TODO Handle shared data, start your process from here
  plan = Planner(bot_loc, blobs, blocks, zones, waypoints, scPlanner, bot_state, qMove_nav)
  plan.test()
  #plan.start()
  
  
if __name__ == "__main__":
  plan = Planner() #will fail... needs waypoints from map.
  plan.start()
