#!/usr/bin/env python
"""Creates shared data structures, then spawns processes for the major robot tasks and passes them 
those data structures."""

errors = { "ERROR_BAD_CWD" : 100, "ERROR_MAP_SCRIPT" : 101 }
errors.update(dict((v,k) for k,v in errors.iteritems())) # Converts errors to a two-way dict

config = { "map_pkl" : "./mapping/map.pkl", "waypoints_pkl" : "./mapping/waypoints.pkl", "map_props_pkl" :
"./mapping/map_prop_vars.pkl", "log_config" : "logging.conf", "map_script" : "./map_script.py", "map_res" : "-r 4",
"map_script_success" : 0, "map_dir" : "./mapping" }

config["chk_res_cmd"] = "head -n 10 " + config["map_dir"] + "/map.pkl | tr \"\n\" \" \" | grep \"S'res' p2 I4\" > /dev/null 2>&1"

# Add mapping to path
import sys
sys.path.append("./mapping")

# Standard library imports
from multiprocessing import Process, Manager, Queue
from subprocess import call
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
    sys.exit(errors["ERROR_BAD_CWD"])

  # Setup logging
  logging.config.fileConfig(config["log_config"])
  logger = logging.getLogger(__name__)
  logger.debug("Logger is set up")

  # Confirm that map data exists and is of the correct resolution
  if not os.path.isfile(config["map_pkl"]) or not os.path.isfile(config["waypoints_pkl"]) \
                                           or not os.path.isfile(config["map_props_pkl"]) \
                                           or os.system(config["chk_res_cmd"]) != 0:
    logger.warn("Map files don't exist or are not of resolution {}. Building...".format(config["map_res"]))

    # Change to mapping directory so map generated map files are stored there. Store old CWD to change back to.
    origCWD = os.getcwd()
    os.chdir(config["map_dir"])

    # Confirm that the map script exists in this directory
    if not os.path.isfile(config["map_script"]):
      logger.critical("Map script {} not found in CWD {}".format(config["map_script"], origCWD))
      sys.exit(errors["ERROR_MAP_SCRIPT"])

    # Run the map script
    rv = call([config["map_script"], config["map_res"]])

    # Change back to original CWD (typically qwe)
    os.chdir(origCWD)

    # Check return value of map script to confirm that it worked
    if rv != config["map_script_success"]:
      logger.critical("Map script returned {}, call was: {} {}".format(rv, config["map_script"], config["map_res"]))
      sys.exit(errors["ERROR_MAP_SCRIPT"])
  else:
    logger.info("Map files already exist and the map is of resolution {}".format(config["map_res"]))

  # Get map, waypoints and map properties
  course_map = mapper.unpickle_map(config["map_pkl"])
  logger.debug("Map unpickled")
  waypoints = mapper.unpickle_waypoints(config["waypoints_pkl"])
  logger.debug("Waypoints unpickled")
  map_properties = mapper.unpickle_map_prop_vars(config["map_props_pkl"])
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

  # Start serial communication to low-level board
  # TODO Create shared structures commands and responses here and pass on to si? Currently it creates them internally.
  si = comm.SerialInterface()  
  si.start() # Displays an error if port not found (not running on Pandaboard)
  logger.debug("Serial interface set up")

  # Start planner process, pass it shared data
  scPlanner = comm.SerialCommand(si.commands, si.responses)  # create one SerialCommand wrapper for each client
  scPlanner.compassReset()
  # NOTE si.commands and si.responses are process-safe shared structures
  pPlanner = Process(target=planner.run, args=(bot_loc, blobs, blocks, zones, waypoints, scPlanner, bot_state, qMove_nav))
  pPlanner.start()
  logger.info("Planner process started")

  # Start vision process, pass it shared data
  scVision = comm.SerialCommand(si.commands, si.responses)
  pVision = Process(target=vision.run, args=(bot_loc, blobs, blocks, zones, corners, waypoints, scVision, bot_state))
  pVision.start()
  logger.info("Vision process started")

  # Start navigator process, pass it shared data
  scNav = comm.SerialCommand(si.commands, si.responses)
  pNav = Process(target=nav.run, args=(bot_loc, qNav_loc, scNav, bot_state, qMove_nav))
  pNav.start()
  logger.info("Navigator process started")

  # Start localizer process, pass it shared data, waypoints, map_properties course_map and queue for talking to nav
  pLocalizer = Process(target=localizer.run, args=(bot_loc, zones, map_properties, course_map, waypoints, qNav_loc, bot_state))
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
  
  scPlanner.quit()
  si.join()
  logger.info("Joined SerialInterface process")
