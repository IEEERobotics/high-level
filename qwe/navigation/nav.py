#!/usr/bin/env python
"""Primary module of navigation package. 

As this develops, it will eventually accept a goalPose from planner, request a currentPose from localizer, then call
SBPL code (C++ made usable in Python by some method) and pass the configuration params. No file will be created and
no subprocess will spawn. The solution generated by SBPL will be returned to nav (not written to a file), and will then
be parsed and handed off to comm. Some additional logic involving issuing steps of the solution to comm, getting results,
checking for the amount of error, notifying localizer, maybe re-planning, and then issuing the next step will need to
be added."""

import logging
import logging.config

class Nav:

  def __init__(self, bot_loc, course_map, waypoints, qNav_loc, si, bot_state, qMove_nav, logger):
    """Setup navigation class

    :param bot_loc: Shared dict updated with best-guess location of bot by localizer
    :param course_map: Map of course
    :param waypoints: Locations of interest on the course
    :param qNav_loc: Multiprocessing.Queue object for passing movement feedback to localizer from navigator
    :param si: Serial interface object for sending commands to low-level boards
    :param bot_state: Dict of information about the current state of the bot (ex macro/micro nav)
    :param qMove_nav: Multiprocessing.Queue object for passing movement commands to navigation (mostly from Planner)
    :param logger: Used for standard Python logging
    """

    logger.info("Nav instantiated")

    # Store passed-in data
    self.bot_loc = bot_loc
    self.course_map = course_map
    self.waypoints = waypoints
    self.qNav_loc = qNav_loc
    self.si = si
    self.bot_state = bot_state
    self.qMove_nav = qMove_nav
    self.logger = logger
    self.logger.debug("Passed-in data stored to Nav object")

  def start(self):
    """Do any setup of nav here"""
    self.logger.info("Started nav")

    # TODO Add setup code here

    # Call main loop that will handle movement commands passed in via qMove_nav
    self.logger.debug("Calling main loop function")
    self.loop()

  def loop(self):
    """Main loop of nav. Blocks and waits for motion commands passed in on qMove_nav"""

    self.logger.debug("Entering loop")
    while True:
      self.qMove_nav.get()
      # TODO Handle movement logic here


def run(bot_loc, course_map, waypoints, qNav_loc, si, bot_state, qMove_nav):
  """Function that accepts initial data from controller and kicks off nav. Will eventually involve instantiating a class.

  :param bot_loc: Shared dict updated with best-guess location of bot by localizer
  :param course_map: Map of course
  :param waypoints: Locations of interest on the course
  :param qNav_loc: Multiprocessing.Queue object for passing movement feedback to localizer from navigator
  :param si: Serial interface object for sending commands to low-level boards
  :param bot_state: Dict of information about the current state of the bot (ex macro/micro nav)
  :param qMove_nav: Multiprocessing.Queue object for passing movement commands to navigation (mostly from Planner)
  """

  # Setup logging
  logging.config.fileConfig("logging.conf")
  logger = logging.getLogger(__name__)
  logger.debug("Logger setup in nav")

  # Build nav object and start it
  logger.debug("Executing run function of nav")
  nav = Nav(bot_loc, course_map, waypoints, qNav_loc, si, bot_state, qMove_nav, logger)
  logger.info("Built Nav object")
  nav.start()
  logger.info("Started nav, exiting run in nav")


