#!/usr/bin/env python
"""Creates shared data structures, then spawns processes for the major robot tasks and passes them 
those data structures."""

# Add mapping to path
import sys
sys.path.append("./mapping")

# Standard library imports
from multiprocessing import Process, Manager, Queue
import time
import logging
import logging.config

# Local module imports
import planning.Planner as planner
import vision.vision as vision
import mapping.pickler as mapper
import localizer.localizer as localizer
import navigation.nav as nav
import comm.serial_interface as comm

if __name__ == "__main__":
  # Setup logging
  logging.config.fileConfig("logging.conf")
  logger = logging.getLogger(__name__)
  logger.debug("Logger setup in controller")

  # Start serial communication to low-level board
  si = comm.SerialInterface()
  si.start() # Displays an error if port not found (not running on Pandaboard)
  logger.info("Serial interface setup")

  # Build shared data structures
  # Not wrapping them in a mutable container, as it's more complex for other devs
  # See the following for details: http://goo.gl/SNNAs
  manager = Manager()
  bot_loc = manager.dict(x=None, y=None, theta=None)
  blocks = manager.list()
  zones = manager.list()
  corners = manager.list()
  bot_state = manager.dict(nav_type=None, action_type=None)
  logger.debug("Shared data structures created")

  # Build Queue objects for IPC. Name shows producer_consumer.
  qNav_loc = Queue()
  qMove_nav = Queue()
  logger.debug("Queue objects created")

  # Get map, waypoints and map properties
  course_map = mapper.unpickle_map("./mapping/map.pkl")
  logger.info("Map unpickled")
  waypoints = mapper.unpickle_waypoints("./mapping/waypoints.pkl")
  logger.info("Waypoints unpickled")
  map_properties = mapper.unpickle_map_prop_vars("./mapping/map_prop_vars.pkl")
  logger.info("Map properties unpickled")

  # Start planner process, pass it shared data
  pPlanner = Process(target=planner.run, args=(bot_loc, blocks, zones, waypoints, si, bot_state, qMove_nav))
  pPlanner.start()
  logger.info("Planner process started")

  # Start vision process, pass it shared data
  pVision = Process(target=vision.run, args=(bot_loc, blocks, zones, corners, waypoints, si, bot_state))
  pVision.start()
  logger.info("Vision process started")

  # Start navigator process, pass it shared data
  pNav = Process(target=nav.run, args=(bot_loc, course_map, waypoints, qNav_loc, si, bot_state, qMove_nav))
  pNav.start()
  logger.info("Navigator process started")

  # Start localizer process, pass it shared data, waypoints, map_properties course_map and queue for talking to nav
  pLocalizer = Process(target=localizer.run, args=(bot_loc, blocks, corners, map_properties, course_map, qNav_loc, si, bot_state))
  pLocalizer.start()
  logger.info("Localizer process started")

  pNav.join()
  logger.info("Joined navigation process")
  pVision.join()
  logger.info("Joined vision process")
  pLocalizer.join()
  logger.info("Joined localizer process")
  pPlanner.join()
  logger.info("Joined planner process")
