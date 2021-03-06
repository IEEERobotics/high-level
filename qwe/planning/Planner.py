"""
Code for python planner
"""

import blockSim as BlockDet
import twoWayDict as twd
import navigation.nav as nav
from datetime import datetime
import comm.serial_interface as comm
import math
import time
import logging.config


pixelsToInches = 0.0195

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
  
  
  def __init__(self, bot_loc, blobs, blocks, zones, waypoints, scPlanner, bot_state, qMove_nav, logger):
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
    self.logger = logger
    
    self.bot_state["cv_blockDetect"] = False
    self.bot_state["cv_lineTrack"] = False
    
    self.armID[0] = comm.right_arm 
    self.armID[1] = comm.left_arm
  
    self.nextSeaLandBlock = ["St01","St02","St03","St04","St05","St06","St07","St08","St09","St10","St11","St12","St13","St14"]
    self.nextAirBlock = []
    self.nextSeaBlockLoc = ["Se01","Se02","Se03","Se04","Se05","Se06"]
    self.nextLandBlockLoc = ["L01","L02","L03","L04","L05","L06"]
    self.colors = ["red", "blue", "green", "orange", "brown", "yellow"]
    
    for i in range(len(self.nextSeaLandBlock)):
      self.zones[i] = 1
    for i in range(len(self.nextSeaBlockLoc)):
      self.zones[i] = 0
    for i in range(len(self.nextLandBlockLoc)):
      self.zones[i] = 0
    for i in range(len(self.colors)):
      self.scannedSeaLocs[self.colors[i]] = "empty"
      self.scannedLandLocs[self.colors[i]] = "empty"

    self.bot_state["zone_change"] = 1
    
  #get current location
  def getCurrentLocation(self):
    return self.bot_loc

  def wait(self, blocking):
    while blocking != False:
      continue
  
  def getBlobNearCenter(self):
    closestBlob = None
    mindist = 641 #some large number at least as large as width of image
    direction = 1
    mindir = direction
    for blob in self.blobs:  # a more pythonic way of iterating
      direction = 1
      x,y,w,h = blob.bbox
      blockDist = (320 - (x + w / 2))  # TODO use SimpleBlob.center instead?
      if blockDist < 0:
        blockDist = blockDist * -1
        direction = -1
      
      if blockDist < mindist:
        mindist = blockDist
        closestBlob = blob
        mindir = direction
    mindist = pixelsToInches * mindist
    return closestBlob, mindir, mindist
  
  #more to the next block - use this if next block location is
  #handled by nav instead of planner
  def moveToNextBlock(self):
    pass
    #print "Moving to Next Block"
    #self.moveTo(self.getCurrentLocation(), "nextblock loc")
    #micro or macro???
  
  #move from start to end
  def moveToWayPoint(self, startLoc, endLoc):
    #print "Moving from ", startLoc, " to ", endLoc, "--", self.waypoints[endLoc]
    self.logger.info("Moving from "+ str(startLoc)+ " to "+str(endLoc)+ "--"+str(self.waypoints[endLoc]))
    x, y = self.waypoints[endLoc][1]
    theta = self.waypoints[endLoc][2]
    speed = self.waypoints[endLoc][3]
    self.bot_state["naving"] = True
    macro_m = nav.macro_move(x, y, theta, datetime.now())
    self.qMove_nav.put(macro_m)
    #self.wait(self.bot_state["naving"])
    while self.bot_state["naving"] != False:
      continue
    
  def microMove(self, distance, direction):
    #print "Moving from ", startLoc, " to ", endLoc
    micro_m = nav.micro_move_XY(distance, comm.default_speed * direction, datetime.now())
    self.qMove_nav.put(micro_m)

  def moveUpRamp(self, loc1, loc2):
    self.logger.info("Moving up the ramp from "+ str(loc1)+ " to "+str(loc2))
    x1, y1 = self.waypoints[loc1][1]
    x2, y2 = self.waypoints[loc2][1]
    distance = math.sqrt((x1-x2)*(x1-x2) + (y1-y2)*(y1-y2))
    speed = comm.default_speed * 1.2
    micro_m = nav.micro_move_XY(distance, speed, datetime.now())
    self.qMove_nav.put(micro_m)
  
  
  def alignWithCenter(self, loc):
    pass
    
    #this is supposed to align with the expected white line... 
    #one possible solution: 
    # a repeated forward and backward micromoves until we are aligned
    
    
    
    #dist = 320-(x+w/2)
    #direction = 1
    #if dist < 0:
    #  direction = -1
    #print "Distance to center: ", dist, "pixels -- ", dist*0.0192, "inches --", dist*0.0192*1622/9.89,"revolutions"
    #self.micromove(dist, direction)

    
  def processSeaLand(self, startTime):
    armCount = 0
    self.armList = []
    self.logger.info("+++++ +++++ Beginning to pick and place sea and land blocks +++++ +++++")
    for i in range(len(self.nextSeaLandBlock)):
    
      elapsedTime = datetime.now() - startTime
      if elapsedTime.seconds > 250:
        self.logger.debug("Don't you have a flight to catch?") #time to start processing air.
        #things to do: if location of both airblocks are known, pick them up, else continue scanning
        # if one of the arms has a block, use the other arm to pick up block, place other block down
        # if both arms have blocks -- this is not good!
      
      stID = self.nextSeaLandBlock[i];
      #print "Processing: [", stID, self.waypoints[stID], "]"
      self.logger.info("Processing: ["+ str(stID)+ str(self.waypoints[stID])+ "]")
      
      #movement along the whiteline, close to the blocks
      self.bot_state["cv_blockDetect"] = False
      self.bot_state["cv_lineTrack"] = True
      self.moveToWayPoint(self.getCurrentLocation(), stID)
      
      #get block from vision, do not track lines
      self.bot_state["cv_blockDetect"] = True
      self.bot_state["cv_lineTrack"] = False
      
      #self.wait(self.bot_state["cv_blockDetect"])
      while self.bot_state["cv_blockDetect"] != False:
        continue
      if self.blobs == None:
        continue
      block, direction, distance = self.getBlobNearCenter()
      
      #block = self.storageSim[i]
      #print "Processing: [", block.getColor(), block.getSize(), block.getLocation(), "]"
         
      #if the block is small, assign that to list of air blocks
      #continue / move to next block
      #if block.getSize() == "small":
      if block.length == "small":
        self.nextAirBlock.append([stID, block])
        continue
      
      #in order to pick up a block, first check if bot is centered
      #self.alignWithCenter()
      self.microMove(distance, direction)
      #self.pickUpBlock(armCount) #arm 0 or 1.
      self.scPlanner.armPick(self.armID[armCount])
      self.zones[stID] = 0
      self.bot_state["zone_change"] = self.bot_state["zone_change"] + 1
      self.armList.append(block)
      armCount = armCount + 1;

      if armCount == 2:
        self.logger.info("picked up 2 blocks")
        
        #when dropping blocks off, offset the center of the bot
        #about 0.5 from the center of the dropoff zone
    
        #Both arms contain sea blocks
        #if self.armList[0].getSize() == "medium" and self.armList[1].getSize() == "medium":
        if self.armList[0].length == "medium" and self.armList[1].length == "medium":
          self.moveToWayPoint(self.getCurrentLocation(), "sea")
          
          self.goToNextSeaDropOff(self.armList[0])
          #self.placeBlock(0)
          self.scPlanner.armDrop(self.armID[0])
          
          self.goToNextSeaDropOff(self.armList[1])
          #self.placeBlock(1)
          self.scPlanner.armDrop(self.armID[1])

        #Both arms contain land blocks
        #elif self.armList[0].getSize() == "large" and self.armList[1].getSize() == "large":
        elif self.armList[0].length == "large" and self.armList[1].length == "large":
          self.moveToWayPoint(self.getCurrentLocation(), "land")
          
          self.goToNextLandDropOff(self.armList[0])
          #self.placeBlock(0)
          self.scPlanner.armDrop(self.armID[0])
          
          self.goToNextLandDropOff(self.armList[1])
          #self.placeBlock(1)
          self.scPlanner.armDrop(self.armID[1])
              
        #One arm contains sea block and other contains land block
        #elif self.armList[0].getSize() == "medium" and self.armList[1].getSize() == "large":
        elif self.armList[0].length == "medium" and self.armList[1].length == "large":
          self.moveToWayPoint(self.getCurrentLocation(), "sea")
          self.goToNextSeaDropOff(self.armList[0])
          #self.placeBlock(0)
          self.scPlanner.armDrop(self.armID[0])
        
          self.moveToWayPoint(self.getCurrentLocation(), "land")
          self.goToNextLandDropOff(self.armList[1])
          #self.placeBlock(1)
          self.scPlanner.armDrop(self.armID[1])
            
        #One arm contains land block and other contains sea block
        #elif self.armList[0].getSize() == "large" and self.armList[1].getSize() == "medium":
        elif self.armList[0].length == "large" and self.armList[1].length == "medium":
          # even if the orders are different, first go to sea then land
          self.moveToWayPoint(self.getCurrentLocation(), "sea")
          self.goToNextSeaDropOff(self.armList[1])
          #self.placeBlock(1)
          self.scPlanner.armDrop(self.armID[1])
        
          self.moveToWayPoint(self.getCurrentLocation(), "land")
          self.goToNextLandDropOff(self.armList[0])
          #self.placeBlock(0)
          self.scPlanner.armDrop(self.armID[0])
                
        armCount = 0
        self.armList = []
        self.logger.info("===== ===== ===== ===== ===== ===== ===== ===== ===== =====")
        self.moveToWayPoint(self.getCurrentLocation(), "storage")
      #end if
    #end for
  #end processSeaLand
        
  def processAir(self):
    for i in range(len(self.nextAirBlock)):
      block = self.nextAirBlock[i];
      #print "Processing: [", block.getColor(), block.getSize(), block.getLocation(), "]"
      #self.pickUpBlock(block.getLocation(), i);
      stID = block[0]
      self.bot_state["cv_blockDetect"] = False
      self.bot_state["cv_lineTrack"] = True
      self.moveToWayPoint(self.getCurrentLocation(), stID)
      
      self.bot_state["cv_blockDetect"] = True
      self.bot_state["cv_lineTrack"] = False
      
      #self.wait(self.bot_state["cv_blockDetect"])
      while self.bot_state["cv_blockDetect"] != False:
        continue
      if self.blobs == None:
        continue
      block, direction, distance = self.getBlobNearCenter()
      
      #in order to pick up a block, first check if bot is centered
      #self.alignWithCenter()
      self.microMove(distance, direction)
            
      self.pickUpBlock(block[0], i);
    #end for
    
    self.logger.info("Move to Ramp, up the ramp, to the drop-off")
    self.moveUpRamp("grnd2ramp","lwrPlt") #up the ramp
    self.moveToWayPoint(self.getLocation(), "lwrPlt") #align in the right direction on lower platform
    self.moveUpRamp("lwrPlt", "air") #up the long ramp
        
    #self.moveToWayPoint(self.getCurrentLocation(), "grnd2ramp") #normal speed
    #self.moveToWayPoint(self.getCurrentLocation(), "lwrPlt") #ramp speed
    #self.moveToWayPint(self.getCurrentLocation(), "uprRamp") #normal speed
    #self.moveToWayPoint(self.getCurrentLocation(), "air") #ramp speed
    
    self.logger.info("Drop Air Blocks")
    
    self.logger.info("Placing First Air Block")
    self.moveToWayPoint(self.getCurrentLocation(), "A01")
    color, direction, distance = self.getAirDropOffColor()  # TODO color may be "none" with invalid direction and distance - take care of that
    if color is not None:
      if color == self.armList[0].color:
        self.placeBlock(0)
      else:
        self.placeBlock(1)
    
    self.logger.info("Placing Second Air Block")
    self.moveToWayPoint(self.getCurrentLocation(), "A02")
    color, direction, distance = self.getAirDropOffColor()
    if color is not None:
      if color == self.armList[0].color:
        self.placeBlock(0)
      else:
        self.placeBlock(1)
    #self.goToNextAirDropOff(self.armList[1])
    #self.placeBlock(1)
    

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
    availList = self.getAvailableSeaDropOffs()
    #blockColor = block.getColor()
    blockColor = block.color
    
    #movement along white lines
    self.bot_state["cv_blockDetect"] = False
    self.bot_state["cv_lineTrack"] = True
    if self.scannedSeaLocs[blockColor] == "empty": 
      #block location unknown
      for i in range(len(availList)):
        self.moveToWayPoint(self.getCurrentLocation(), availList[i])
        
        #get the color at waypoint from vision
        self.bot_state["cv_blockDetect"] = True
        self.bot_state["cv_lineTrack"] = False
        
        #self.wait(self.bot_state["cv_blockDetect"])
        while self.bot_state["cv_blockDetect"] != False:
          continue
        if self.blobs == None:
          continue
        
        #color = seaBlockSim[availList[i]]
        zone, direction, distance = self.getBlobNearCenter()
        color = zone.color
                
        if color == blockColor:
          #found color
          #align with center
          #TODO :add condition for when distacne is less than a particular val
          #and, to micromove based on which arm is being lowered.
          self.zones[ availList[i]] = 1
          self.bot_state["zone_change"] = self.bot_state["zone_change"] + 1
          self.microMove(distance, direction)
          break
        else:
          self.scannedSeaLocs[color] = availList[i]
        #end if-else
      #end for     
    else:
      self.moveToWayPoint(self.getCurrentLocation(), self.scannedSeaLocs[blockColor])
      self.zones[self.scannedSeaLocs[blockColor]] = 1
      self.bot_state["zone_change"] = self.bot_state["zone_change"] + 1

  #go to the next land dropoff zone
  #separate function to handle land specific movements
  def goToNextLandDropOff(self, block):
    availList = self.getAvailableLandDropOffs()
    #blockColor = block.getColor()
    blockColor = block.color
    
    #movement along white lines
    self.bot_state["cv_blockDetect"] = False
    self.bot_state["cv_lineTrack"] = True
    if self.scannedLandLocs[blockColor] == "empty": 
      #block location unknown
      for i in range(len(availList)):
        self.moveToWayPoint(self.getCurrentLocation(), availList[i])
        
        #get the color at waypoint from vision
        self.bot_state["cv_blockDetect"] = True
        self.bot_state["cv_lineTrack"] = False
        
        #self.wait(self.bot_state["cv_blockDetect"])
        while self.bot_state["cv_blockDetect"] != False:
          continue
        if self.blobs == None:
          continue
        
        #color = LandBlockSim[availList[i]]
        zone, direction, distance = self.getBlobNearCenter()
        color = zone.color
        
        if color == blockColor:
          #found color
          #align with center
          #TODO :add condition for when distacne is less than a particular val
          #and, to micromove based on which arm is being lowered.
          self.microMove(distance, direction)
          self.zones[availList[i]] = 1
          self.bot_state["zone_change"] = self.bot_state["zone_change"] + 1
          break
        else:
          self.scannedLandLocs[color] = availList[i]
          
    else:
      self.moveToWayPoint(self.getCurrentLocation(), self.scannedLandLocs[blockColor])
      self.zones[self.scannedLandLocs[blockColor]] = 1
      self.bot_state["zone_change"] = self.bot_state["zone_change"] + 1
  
  
  def getAirDropOffColor(self):
    self.bot_state["cv_blockDetect"] = True
    self.bot_state["cv_lineTrack"] = False
    
    #self.wait(self.bot_state["cv_blockDetect"])
    while self.bot_state["cv_blockDetect"] != False:
      continue
    if self.blobs == None:
      return None, direction, distance
    
    #color = LandBlockSim[availList[i]]
    zone, direction, distance = self.getBlobNearCenter()
    color = zone.color if zone is not None else "none"
    return color, direction, distance
    #pass
  
  
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
    #self.storageSimulator("storage") ##use when vision is not available
    #self.dropOffSimulator("sea") ##use when vision is not available
    #self.dropOffSimulator("land")
    self.logger.info("Move to Storage Start")
    
    startTime = datetime.now()
    
    self.moveToWayPoint(self.getCurrentLocation(), "storage")
    #print "Scan Storage"
    #self.scanStorageFirstTime("storage") # BUG: This should not be hardcoded. Currently fails.
    #print "Move to Storage Start"
    #self.moveToWayPoint(self.getCurrentLocation(), "storage")
    print "***********************************************"
    print "********** Processing - Sea and Land **********"
    print "***********************************************"
    self.processSeaLand(startTime)
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
      

def run(bot_loc, blobs, blocks, zones, waypoints, scPlanner, bot_state, qMove_nav, logger=None):
  
  if logger is None:
    logging.config.fileConfig("logging.conf") # TODO This will break if not called from qwe. Add check to fix based on cwd?
    logger = logging.getLogger(__name__)
    logger.debug("Logger is set up")
  
  logger.debug("Executing run function of Planner")
  plan = Planner(bot_loc, blobs, blocks, zones, waypoints, scPlanner, bot_state, qMove_nav, logger)
  #plan.test()
  plan.start()
  logger.debug("Completed Planner Execution")
  
if __name__ == "__main__":
  plan = Planner() #will fail... needs waypoints from map.
  plan.start()
