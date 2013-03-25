#!/usr/bin/env python

# Standard library imports
import unittest
import sys
import logging
import logging.config
from multiprocessing import Process, Manager, Queue
import os

ERROR_BAD_CWD = 100

# Find path to ./qwe directory. Allows for flexibility in the location tests are fired from.
if os.getcwd().endswith("high-level/qwe"):
  path_to_qwe = "./"
elif os.getcwd().endswith("high-level/qwe/navigation"):
  path_to_qwe = "../"
elif os.getcwd().endswith("high-level/qwe/navigation/tests"):
  path_to_qwe = "../../"
else:
  sys.exit(ERROR_BAD_CWD)

sys.path.append(path_to_qwe) # Makes local module imports work as if in qwe
sys.path.append(path_to_qwe + "mapping") # Makes map unpickle work

# Local module imports
import mapping.pickler as mapper
import navigation.nav as nav
import comm.serial_interface as comm

class TestSolutionGeneration(unittest.TestCase):

  def setUp(self):
    """Create nav object and feed it appropriate data"""
    
    # Create file and stream handlers
    file_handler = logging.handlers.RotatingFileHandler(path_to_qwe + "logs/unittests.log", maxBytes=512000, backupCount=50)
    file_handler.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.WARN)

    # Create formatter and add to handlers
    formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    # Create logger and add handlers
    self.logger = logging.getLogger("unittest")
    self.logger.setLevel(logging.DEBUG)
    self.logger.addHandler(file_handler)
    self.logger.addHandler(stream_handler)
    self.logger.debug("Logger is set up")
     
    # Start serial communication to low-level board
    self.si = comm.SerialInterface()
    self.si.start() # Displays an error if port not found (not running on Pandaboard)

    # Build shared data structures
    self.manager = Manager()
    self.bot_loc = self.manager.dict(x=None, y=None, theta=None)
    self.bot_state = self.manager.dict(nav_type=None, action_type=None)

    # Build Queue objects for IPC. Name shows producer_consumer.
    self.qNav_loc = Queue()
    self.qMove_nav = Queue()

    # Get map, waypoints and map properties
    self.course_map = mapper.unpickle_map(path_to_qwe + "mapping/map.pkl")
    self.waypoints = mapper.unpickle_waypoints(path_to_qwe + "mapping/waypoints.pkl")

    # Build nav object
    self.Nav = nav.Nav(self.bot_loc, self.course_map, self.waypoints, self.qNav_loc, self.si, self.bot_state, self.qMove_nav, \
    self.logger)

if __name__ == "__main__":
  unittest.main()
