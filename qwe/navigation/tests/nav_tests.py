#!/usr/bin/env python

# Standard library imports
import unittest
import sys
import logging
import logging.config
from multiprocessing import Process, Manager, Queue
import os

# Dict of error codes and their human-readable names
errors = {100 : "ERROR_BAD_CWD"}
errors.update(dict((v,k) for k,v in errors.iteritems())) # Converts errors to a two-way dict

# Find path to ./qwe directory. Allows for flexibility in the location tests are fired from.
if os.getcwd().endswith("qwe"):
  path_to_qwe = "./"
elif os.getcwd().endswith("qwe/navigation"):
  path_to_qwe = "../"
elif os.getcwd().endswith("qwe/navigation/tests"):
  path_to_qwe = "../../"
else:
  print "Error: Bad CWD" 
  sys.exit(errors["ERROR_BAD_CWD"])

sys.path.append(path_to_qwe) # Makes local module imports work as if in qwe
sys.path.append(path_to_qwe + "mapping") # Makes map unpickle work

# Local module imports
import mapping.pickler as mapper
import navigation.nav as nav
import comm.serial_interface as comm

# Paths to various files from qwe
path_to_env = path_to_qwe + "navigation/envs/env.cfg"
path_to_sbpl = path_to_qwe + "navigation/cmake_build/bin/test_sbpl"
path_to_sol = path_to_qwe + "navigation/sols/sol.txt"

class TestFileGeneration(unittest.TestCase):

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
    # FIXME Currently, SIs threads hang and prevent tests from finishing
    self.si = comm.SerialInterface()
    #self.si.start() # Displays an error if port not found (not running on Pandaboard)
    self.logger.info("Serial interface set up")

    # Build shared data structures
    self.manager = Manager()
    self.bot_loc = self.manager.dict(x=.11, y=.11, theta=0) # Same params used in the env1.txt example file
    self.bot_state = self.manager.dict(nav_type=None, action_type=None)
    self.logger.debug("Shared data structures created")

    # Build Queue objects for IPC. Name shows producer_consumer.
    self.qNav_loc = Queue()
    self.qMove_nav = Queue()
    self.logger.debug("Queue objects created")

    # Get map, waypoints and map properties
    self.course_map = mapper.unpickle_map(path_to_qwe + "mapping/map.pkl")
    self.logger.info("Map unpickled")
    self.waypoints = mapper.unpickle_waypoints(path_to_qwe + "mapping/waypoints.pkl")
    self.logger.info("Waypoints unpickled")

    # Build nav object
    self.Nav = nav.Nav(self.bot_loc, self.course_map, self.waypoints, self.qNav_loc, self.si, self.bot_state, self.qMove_nav, \
      self.logger)
    self.logger.info("Nav object instantiated")

  def test_env_file_generation(self):
    """Delete environment file and then generate it, to confirm that it's created"""

    # Check if env file already exits and if it does delete it
    if os.path.isfile(path_to_env):
      os.remove(path_to_env)
      self.logger.info("Environment file existed and was removed")
    else:
      self.logger.info("No environment file existed before test")

    # Call Nav.start to setup Nav, but don't enter queue blocking loop
    start_rv = self.Nav.start(doLoop=False)

    # Check return value of call to Nav.start
    if start_rv is not None:
      self.logger.error("Return value of Nav.start was: " + nav.errors[start_rv])
    self.assertTrue(start_rv is None, "Nav.start returned " + str(start_rv))

    # Generate env file
    genSol_rv = self.Nav.genSol(.35, .3, 0) # Same params used in the env1.txt example file

    # Check return value of call to Nav.genSol
    if type(genSol_rv) is not list and genSol_rv in nav.errors:
      self.logger.error("Return value of Nav.genSol was: " + nav.errors[genSol_rv])
      self.assertTrue(genSol_rv not in nav.errors, "Nav.genSol failed with " + nav.errors[genSol_rv])

    # Confirm that env file was generated
    self.assertTrue(os.path.isfile(path_to_env), "Env file not found at " + path_to_env)

if __name__ == "__main__":
  unittest.main() # Execute all tests
