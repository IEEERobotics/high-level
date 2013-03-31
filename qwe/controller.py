#!/usr/bin/env python
"""Creates shared data structures, then spawns processes for the major robot tasks and passes them 
those data structures."""

ERROR_BAD_CWD = 100

# Add mapping to path
import sys
sys.path.append("./mapping")

# Standard library imports
from multiprocessing import Process, Manager, Queue
import logging.config
import os
from datetime import datetime

# Local module imports
import planning.Planner as planner
import vision.vision as vision
import mapping.pickler as mapper
import localizer.localizer as localizer
import navigation.nav as nav
import comm.serial_interface as comm

if __name__ == "__main__":
  # Confirm that controller is being run from correct directory
  if not os.getcwd().endswith("qwe"):
    print "Run me from ./qwe"
    sys.exit(ERROR_BAD_CWD)

  # Setup logging
  logging.config.fileConfig("logging.conf")
  logger = logging.getLogger(__name__)
  logger.debug("Logger is set up")

  # Start serial communication to low-level board
  # TODO Create shared structures commands and responses here and pass on to si? Currently it creates them internally.
  si = comm.SerialInterface()  
  si.start() # Displays an error if port not found (not running on Pandaboard)
  logger.debug("Serial interface set up")

  # Get map, waypoints and map properties
  course_map = mapper.unpickle_map("./mapping/map.pkl")
  logger.debug("Map unpickled")
  waypoints = mapper.unpickle_waypoints("./mapping/waypoints.pkl")
  logger.debug("Waypoints unpickled")
  map_properties = mapper.unpickle_map_prop_vars("./mapping/map_prop_vars.pkl")
  logger.debug("Map properties unpickled")

  # Find start location
  start_x = waypoints["start"][0][0] * float(nav.env_config["cellsize"]) * 39.3701 # Convert to inches
  start_y = waypoints["start"][0][1] * float(nav.env_config["cellsize"]) * 39.3701 # Convert to inches
  start_theta = 0 # In radians

  # Build shared data structures
  # Not wrapping them in a mutable container, as it's more complex for other devs
  # See the following for details: http://goo.gl/SNNAs
  manager = Manager()
  bot_loc = manager.dict(x=start_x, y=start_y, theta=start_theta, dirty=False)
  blobs = manager.list()  # for communication between vision and planner
  blocks = manager.dict()
  zones = manager.dict()
  corners = manager.list()
  bot_state = manager.dict(nav_type=None, action_type=None, naving=False) #nav_type is "micro" or "macro"
  logger.debug("Shared data structures created")

  # Build Queue objects for IPC. Name shows producer_consumer.
  qNav_loc = Queue()
  qMove_nav = Queue()
  logger.debug("Queue objects created")

  # Start planner process, pass it shared data
  scPlanner = comm.SerialCommand(si.commands, si.responses)  # create one SerialCommand wrapper for each client
  # NOTE si.commands and si.responses are process-safe shared structures
  pPlanner = Process(target=planner.run, args=(bot_loc, blobs, blocks, zones, waypoints, scPlanner, bot_state, qMove_nav))
  pPlanner.start()
  logger.info("Planner process started")

  # Start vision process, pass it shared data
  scVision = comm.SerialCommand(si.commands, si.responses)
  pVision = Process(target=vision.run, args=(bot_loc, blobs, blocks, zones, corners, waypoints, scVision, bot_state))
  #pVision.start()
  logger.info("Vision process started")

  # Start navigator process, pass it shared data
  scNav = comm.SerialCommand(si.commands, si.responses)
  pNav = Process(target=nav.run, args=(bot_loc, course_map, waypoints, qNav_loc, scNav, bot_state, qMove_nav))
  pNav.start()
  logger.info("Navigator process started")

  # Start localizer process, pass it shared data, waypoints, map_properties course_map and queue for talking to nav
  pLocalizer = Process(target=localizer.run, args=(bot_loc, blocks, map_properties, course_map, qNav_loc, bot_state))
  pLocalizer.start()
  logger.info("Localizer process started")

  pNav.join()
  logger.info("Joined navigation process")
  #pVision.join()
  logger.info("Joined vision process")
  pLocalizer.join()
  logger.info("Joined localizer process")
  pPlanner.join()
  logger.info("Joined planner process")
  
  scPlanner.quit()
  si.join()
  logger.info("Joined SerialInterface process")
