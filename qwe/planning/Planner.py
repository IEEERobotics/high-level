"""
Code for python planner
"""

import blockSim as BlockDet
import twoWayDict as twd
import navigation.nav as nav
from datetime import datetime
import comm.serial_interface as comm

class Planner:
  nextSeaLandBlock = [] #list of the next available sea or land block to pick up
  nextAirBlock = [] #list of the 2 air blocks in storage
  armList = [] #list of which arm contains what
  armID = [2, 0]  # armID[0] = right arm, armID[1] = left arm

  storageSim = []
  seaBlockSim = {}
  landBlockSim = {}
  airBlockSim = []
	
  nextSeaBlockLoc = []
  nextLandBlockLoc = []
  nextAirBlockLoc = []
  
  scannedSeaLocs = {}
  scannedLandLocs = {}
  colors = []
  #nsbl = twd.TwoWayDict()
  #nlbl = twd.TwoWayDict()
  
  
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
    
    self.armID[0] = comm.right_arm 
    self.armID[1] = comm.left_arm
  
    self.nextSeaLandBlock = ["St01","St02","St03","St04","St05","St06","St07","St08","St09","St10","St11","St12","St13","St14"]
    self.nextAirBlock = []
    self.nextSeaBlockLoc = ["Se01","Se02","Se03","Se04","Se05","Se06"]
    self.nextLandBlockLoc = ["L01","L02","L03","L04","L05","L06"]
    self.colors = ["red", "blue", "green", "orange", "brown", "yellow"]
    
    for i in range(len(self.nextSeaLandBlock)):
      self.blocks[i] = 1
    for i in range(len(self.nextSeaBlockLoc)):
      self.zones[i] = 0
    for i in range(len(self.nextLandBlockLoc)):
      self.zones[i] = 0
    for i in range(len(self.colors)):
      self.scannedSeaLocs[self.colors[i]] = "empty"
      self.scannedLandLocs[self.colors[i]] = "empty"
    
  #get current location
  def getCurrentLocation(self):
    return self.bot_loc

  #more to the next block - use this if next block location is
  #handled by nav instead of planner
  def moveToNextBlock(self):
    print "Moving to Next Block"
    self.moveTo(self.getCurrentLocation(), "nextblock loc")
    #micro or macro???
  
  #move from start to end
  def moveToWayPoint(self, startLoc, endLoc):
    print "Moving from ", startLoc, " to ", endLoc, "--", self.waypoints[endLoc]
    x, y = self.waypoints[endLoc][1]
    theta = self.waypoints[endLoc][2]
    speed = self.waypoints[endLoc][3]
    self.bot_state["naving"] = True
    macro_m = nav.macro_move(x, y, theta, datetime.now())
    self.qMove_nav.put(macro_m)
    while self.bot_state["naving"] != False:
      continue

  def moveTo(Self, startLoc, endLoc):
    print "Moving from ", startLoc, " to ", endLoc
    #micro_m = nav.micro_move(x, y, theta, datetime.now())
    #self.qMove_nav.put(micro_m)
    
  def processSeaLand(self):
    armCount = 0
    armList = []
    print "+++++ +++++ +++++ +++++ +++++ +++++"
    for i in range(len(self.nextSeaLandBlock)):
      stID = self.nextSeaLandBlock[i];
      print "Processing: [", stID, self.waypoints[stID], "]"
      self.moveToWayPoint(self.getCurrentLocation(), stID)
      
      #get block from vision
      block = self.storageSim[i]
      #print "Processing: [", block.getColor(), block.getSize(), block.getLocation(), "]"
           
      #if the block is small, assign that to list of air blocks
      #continue / move to next block
      if block.getSize() == "small":
        self.nextAirBlock.append(block)
        continue
      
      #in order to pick up a block, first check if bot is centered
      #that code can exist in pickUpBlock().
      self.pickUpBlock(armCount) #arm 0 or 1.
      armList.append(block)
      armCount = armCount + 1;

      if armCount == 2:
        print "picked up 2 blocks"
        
        #Both arms contain sea blocks
        if armList[0].getSize() == "medium" and armList[1].getSize() == "medium":
          self.moveToWayPoint(self.getCurrentLocation(), "sea")
          
          goToNextDropOff(armList[0], "sea")
          self.placeBlock(0)
          
          goToNextDropOff(armList[1], "sea")
          self.placeBlock(1)

        #Both arms contain land blocks
        elif armList[0].getSize() == "large" and armList[1].getSize() == "large":
          self.moveToWayPoint(self.getCurrentLocation(), "land")
          
          goToNextDropOff(armList[0], "land")
          self.placeBlock(0)
          
          armId = goToNextDropOff(armList[1], "land")
          self.placeBlock(1)
              
        #One arm contains sea block and other contains land block
        elif armList[0].getSize() == "medium" and armList[1].getSize() == "large":
          self.moveToWayPoint(self.getCurrentLocation(), "sea")
          goToNextDropOff(armList, "sea")
          self.placeBlock(0)
        
          self.moveToWayPoint(self.getCurrentLocation(), "land")
          goToNextDropOff(armList, "land")
          self.placeBlock(1)
            
        #One arm contains land block and other contains sea block
        elif armList[0].getSize() == "large" and armList[1].getSize() == "medium":
          # even if the orders are different, first go to sea then land
          self.moveToWayPoint(self.getCurrentLocation(), "sea")
          goToNextDropOff(armList[1], "sea")
          self.placeBlock(1)
        
          self.moveToWayPoint(self.getCurrentLocation(), "land")
          goToNextDropOff(armList[0], "land")
          self.placeBlock(0)
                
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

  def getAvailableSeaDropOffs():
    availList = []
    for i in range(len(nextSeaBlockLoc)):
      if zones[nextSeaBlockLoc[i]] == 0:
        availList.append(nextSeaBlockLoc[i])
    return availList

  def getAvailableLandDropOffs():
    availList = []
    for i in range(len(nextLandBlockLoc)):
      if zones[nextLandBlockLoc[i]] == 0:
        availList.append(nextLandBlockLoc[i])
    return availList
  
  #go to the next sea dropoff zone
  #separate function to handle sea specific movements
  def goToNextSeaDropOff(self, block):
    # if seaDropLocList is empty, go to Se01
    # else, check if color of either block matches
    availList = getAvailableSeaDropOffs()
    blockColor = block.getColor()
    
    if scannedSeaLocs[blockColor] == "empty": 
      #block location unknown
      for i in range(len(availList)):
        self.moveToWayPoint(self.getCurrentLocation(), availList[i])
        #get the color at waypoint
        color = seaBlockSim[availList[i]]
        if color == blockColor:
          #found color
          break
        else:
          scannedSeaLocs[color] = availList[i]
          
    else:
      self.moveToWayPoint(self.getCurrentLocation(), scannedSeaLocs[blockColor])

  #go to the next land dropoff zone
  #separate function to handle land specific movements
  def goToNextLandDropOff(self, block):
    availList = getAvailableLandDropOffs()
    blockColor = block.getColor()
    
    if scannedLandLocs[blockColor] == "empty": 
      #block location unknown
      for i in range(len(availList)):
        self.moveToWayPoint(self.getCurrentLocation(), availList[i])
        #get the color at waypoint
        color = LandBlockSim[availList[i]]
        if color == blockColor:
          #found color
          break
        else:
          scannedLandLocs[color] = availList[i]
          
    else:
      self.moveToWayPoint(self.getCurrentLocation(), scannedLandLocs[blockColor])

  # pick up a block given armID
  def pickUpBlock(self, arm):
    armId = self.armID[arm]    
    #self.moveTo(self.getCurrentLocation(), blockLoc)
    #print "Picking Up Block at ", blockLoc, "with Arm", armId
    #call vision to make sure we are centered on the block
    #if we are not centered, micromove
    self.scPlanner.gripperOpen(armId)
    self.scPlanner.armDown(armId)
    self.scPlanner.gripperClose(armId)
    self.scPlanner.armUp(armId)

  # place a block given armID    
  def placeBlock(self, arm):
    armId = self.armID[arm]
    #self.moveTo(self.getCurrentLocation(), blockLoc)
    #print "Placing block from ", self.armID[arm], "at", blockLoc
    #call vision to make sure we are centered on the block
    #if we are not centered, micromove
    self.scPlanner.armDown(armId)
    self.scPlanner.gripperOpen(armId)
    self.scPlanner.armUp(armId)
    self.scPlanner.gripperClose(armId)

  #main
  def start(self):
    self.storageSimulator("storage") ##use when vision is not available
    self.dropOffSimulator("sea") ##use when vision is not available
    self.dropOffSimulator("land")
    print "Move to Storage Start"
    self.moveToWayPoint(self.getCurrentLocation(), "storage")
    #print "Scan Storage"
    #self.scanStorageFirstTime("storage") # BUG: This should not be hardcoded. Currently fails.
    #print "Move to Storage Start"
    #self.moveToWayPoint(self.getCurrentLocation(), "storage")
    print "***********************************************"
    print "********** Processing - Sea and Land **********"
    print "***********************************************"
    self.processSeaLand()
    print "**************************************"
    print "********** Processing - Air **********"
    print "**************************************"
    self.processAir()
    
  def test(self):
    print self.waypoints
    print len(self.waypoints)
    print self.waypoints["storage"]
      
  # Scan the given location for the first time
  # use this if scanning first then dropping blocks
  # def scanFirstTime(self, loc):
#     print "Scanning Storage"    
#     print "Initiating Storage Scan"
#     print "updating list of sea, land and air blocks"
#       
#     count = 0
#     if loc == "storage":
#       count = 14
#     else:
#       count = 6
# 
#     #Scan all blocks in area
#     for i in range(count):
#       #replace blocksim with block detector code
#       bs = BlockDet.BlockSim()
#       block = bs.process(loc,i)
#       ## possibly update block location here
#       ## block.setLocation(self.getCurrentLocation());
#       print "scanning block", i+1, ":", block.getColor(), block.getSize(), block.getLocation()
#       
#       if loc == "storage":
#         if block.getSize() == "small":
#           self.nextAirBlock.append(block)
#         else:
#           self.nextSeaLandBlock.append(block)
#       elif loc == "land":
#         self.nextLandBlockLoc.append(block)
#       elif loc == "sea":
#         self.nextSeaBlockLoc.append(block)
#       # Update target location for next block
# 
#       nextLoc = block.getLocation();
#       bLoc = [int(nextLoc[0]), int(nextLoc[1])]
#       bLoc[1] = bLoc[1] + 2; # change 2 to appropriate value
#         
#       self.moveTo(self.getCurrentLocation(), bLoc)
    #end for
    #print self.nextAirBlock
    #print self.nextSeaLandBlock
  #end scanFirstTime

  # use this if dropping off blocks during scan
  def storageSimulator(self, loc):
    print "-- Using Block Detection Simulator"
    #Scan all 14 blocks in storage area
    for i in range(14):
      bs = BlockDet.BlockSim()
      block = bs.process(loc,i)
      self.storageSim.append(block)
    #end for
  #end scanStorageFirstTime

  # use this if dropping off blocks during scan
  def dropOffSimulator(self, loc):
    print "-- Using Zone Dection Simulator"
    print "Initiating", loc, "scan"      
    for i in range(6):
      print "scanning", loc, "block location", i+1

      bs = BlockDet.BlockSim()
      blockLoc = bs.process(loc,i)
      
      if loc == "land":
        self.landBlockSim[blockLoc.getLocation()] = blockLoc.getColor()
        #self.nlbl[blockLoc.getColor()] = blockLoc.getLocation()
      elif loc == "sea":
        self.seaBlockSim[blockLoc.getLocation()] = blockLoc.getColor()
        #self.nsbl[blockLoc.getColor()] = blockLoc.getLocation()
    #end if
  #end scanLandorSeaFirstTime
      

def run(bot_loc, blobs, blocks, zones, waypoints, scPlanner, bot_state, qMove_nav):
  # TODO Handle shared data, start your process from here
  plan = Planner(bot_loc, blobs, blocks, zones, waypoints, scPlanner, bot_state, qMove_nav)
  #plan.test()
  plan.start()
  
  
if __name__ == "__main__":
  plan = Planner() #will fail... needs waypoints from map.
  plan.start()
