#!/usr/bin/env python
"""Creates shared data structures, then spawns processes for the major robot tasks and passes them 
those data structures."""

# Standard library imports
from multiprocessing import Process, Manager
import time

# Local module imports
import planning.Planner as planner
import vision.vision as vision
import mapping.map_script
# TODO Import localizer entry module
# TODO Import navigation entry module
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
  waypoints = manager.list()

  # Get map and waypoints TODO main() should return these objects
  #course_map, tmp_waypoints = map_script.main()
  #waypoints.extend(tmp_waypoints)

  # Start planner process, pass it shared_data
  pPlanner = Process(target=planner.run, args=(bot_loc, blocks, zones, corners, waypoints))
  pPlanner.start()

  # Start vision process, pass it shared_data TODO Need target
  pVision = Process(target=vision.run, args=(bot_loc, blocks, zones, corners, waypoints))
  pVision.start()

  # Start navigator process, pass it shared_data TODO Need target
  #pNav = Process(target=None, args=(bot_loc, blocks, zones, corners, waypoints))

  # Start localizer process, pass it shared_data and course_map TODO Need target
  #pLocalizer = Process(target=None, args=(bot_loc, blocks, zones, corners, waypoints, course_map))

  #pNav.join()
  pVision.join()
  #pLocalizer.join()
  pPlanner.join()
