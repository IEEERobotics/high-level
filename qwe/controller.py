#!/usr/bin/env python
"""Creates shared data structures, then spawns processes for the major robot tasks and passes them 
those data structures."""

# Standard library imports
from multiprocessing import Process, Manager, Queue

# Local module imports
import planning.Planner as planner
import vision.vision as vision
import mapping.pickler as mapper
import localizer.localizer as localizer
import navigation.nav as nav
# TODO Import comm entry module

if __name__ == "__main__":
  # Build shared data structures
  # Not wrapping them in a mutable container, as it's more complex for other devs
  # See the following for details: http://goo.gl/SNNAs
  manager = Manager()
  bot_loc = manager.dict(x=None, y=None, theta=None)
  blocks = manager.list()
  zones = manager.list()
  corners = manager.list()
  waypoints = manager.list() #TODO Does this really need to be a shared variable?

  # Build Queue objects for IPC. Name shows producer_consumer.
  # Queue for passing motion feedback to localizer. 
  qNav_loc = Queue()

  # Get map, waypoints and map properties
  course_map = mapper.unpickle_map("./mapping/map.pkl")
  tmp_waypoints = mapper.unpickle_waypoints("./mapping/waypoints.pkl")
  map_properties = mapper.unpickle_map_prop_vars("./mapping/map_prop_vars.pkl")
  waypoints.extend(tmp_waypoints)

  # Start planner process, pass it shared_data
  pPlanner = Process(target=planner.run, args=(bot_loc, blocks, zones, corners, waypoints))
  pPlanner.start()

  # Start vision process, pass it shared_data
  pVision = Process(target=vision.run, args=(bot_loc, blocks, zones, corners, waypoints))
  pVision.start()

  # Start navigator process, pass it shared_data
  #pNav = Process(target=nav.run, args=(bot_loc, blocks, zones, corners, course_map, waypoints))
  #pNav.start()

  # Start localizer process, pass it shared_data and course_map
  pLocalizer = Process(target=localizer.run, args=(bot_loc, blocks, zones, corners, waypoints, course_map, qNav_loc))
  pLocalizer.start()

  #pNav.join()
  pVision.join()
  pLocalizer.join()
  pPlanner.join()
