#!/usr/bin/env python

# Standard library imports
import unittest
import sys
import logging
import logging.config
from multiprocessing import Process, Manager, Queue
import os
import pprint as pp
from datetime import datetime
from time import sleep

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
path_to_sbpl = path_to_qwe + "navigation/sbpl/cmake_build/bin/test_sbpl"
path_to_sol = path_to_qwe + "navigation/sols/sol.txt"

class TestFileGeneration(unittest.TestCase):

  def setUp(self):
    """Create nav object and feed it appropriate data"""
    
    # Create file and stream handlers
    self.file_handler = logging.handlers.RotatingFileHandler(path_to_qwe + "logs/unittests.log", maxBytes=512000, backupCount=50)
    self.file_handler.setLevel(logging.DEBUG)
    self.stream_handler = logging.StreamHandler()
    self.stream_handler.setLevel(logging.WARN)

    # Create formatter and add to handlers
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(filename)s | %(funcName)s | %(lineno)d | %(message)s')
    self.file_handler.setFormatter(formatter)
    self.stream_handler.setFormatter(formatter)

    # Create logger and add handlers
    self.logger = logging.getLogger("unittest")
    self.logger.setLevel(logging.DEBUG)
    self.logger.addHandler(self.file_handler)
    self.logger.addHandler(self.stream_handler)
    self.logger.debug("Logger is set up")
     
    # Start serial communication to low-level board
    self.si = comm.SerialInterface()
    self.si.start() # Displays an error if port not found (not running on Pandaboard)
    self.logger.info("Serial interface set up")

    # Build Queue objects for IPC. Name shows producer_consumer.
    self.qNav_loc = Queue()
    self.qMove_nav = Queue()
    self.logger.debug("Queue objects created")

    # Get map, waypoints and map properties
    self.course_map = mapper.unpickle_map(path_to_qwe + "mapping/map.pkl")
    self.logger.info("Map unpickled")
    self.waypoints = mapper.unpickle_waypoints(path_to_qwe + "mapping/waypoints.pkl")
    self.logger.info("Waypoints unpickled")

    # Build shared data structures
    self.manager = Manager()
    start_x = self.waypoints["start"][0][0] * float(nav.env_config["cellsize"]) * 39.3701
    start_y = self.waypoints["start"][0][1] * float(nav.env_config["cellsize"]) * 39.3701
    self.bot_loc = self.manager.dict(x=start_x, y=start_y, theta=0)
    self.bot_state = self.manager.dict(nav_type=None, action_type=None)
    self.logger.debug("Shared data structures created")

    # Build nav object
    self.scNav = comm.SerialCommand(self.si.commands, self.si.responses)
    self.Nav = nav.Nav(self.bot_loc, self.course_map, self.waypoints, self.qNav_loc, self.scNav, self.bot_state, self.qMove_nav, \
      self.logger)
    self.logger.info("Nav object instantiated")

  def tearDown(self):
    """Close serial interface threads"""

    self.logger.removeHandler(self.file_handler)
    self.logger.removeHandler(self.stream_handler)

    self.scNav.quit()
    self.si.join()

  def test_env_and_sol_file_generation(self):
    """Delete environment file and then generate it, to confirm that it's created"""

    # Check if env file already exits and if it does delete it
    if os.path.isfile(path_to_env):
      os.remove(path_to_env)
      self.logger.info("Environment file existed and was removed")
    else:
      self.logger.info("No environment file existed before test")

    # Check if sol file already exits and if it does delete it
    if os.path.isfile(path_to_sol):
      os.remove(path_to_sol)
      self.logger.info("Solution file existed and was removed")
    else:
      self.logger.info("No solution file existed before test")

    # Call Nav.start to setup Nav, but don't enter queue blocking loop
    start_rv = self.Nav.start(doLoop=False)

    # Check return value of call to Nav.start
    if start_rv is not None:
      self.logger.error("Return value of Nav.start was: " + nav.errors[start_rv])
    self.assertTrue(start_rv is None, "Nav.start returned " + str(start_rv))

    # Generate env file
    end_x =  self.waypoints["grnd2ramp"][0][0]* float(nav.env_config["cellsize"])
    end_y =  self.waypoints["grnd2ramp"][0][1]* float(nav.env_config["cellsize"])
    genSol_rv = self.Nav.genSol(end_x, end_y, 0)

    # Check return value of call to Nav.genSol
    if type(genSol_rv) is not list and genSol_rv in nav.errors:
      self.logger.error("Return value of Nav.genSol was: " + nav.errors[genSol_rv])
      self.assertTrue(genSol_rv not in nav.errors, "Nav.genSol failed with " + nav.errors[genSol_rv])

    # Confirm that env file was generated
    self.assertTrue(os.path.isfile(path_to_env), "Env file not found at " + path_to_env)


class TestFullInteraction(unittest.TestCase):

  def setUp(self):
    """Create nav object and feed it appropriate data"""
    
    # Create file and stream handlers
    self.file_handler = logging.handlers.RotatingFileHandler(path_to_qwe + "logs/unittests.log", maxBytes=512000, backupCount=50)
    self.file_handler.setLevel(logging.DEBUG)
    self.stream_handler = logging.StreamHandler()
    self.stream_handler.setLevel(logging.WARN)

    # Create formatter and add to handlers
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(filename)s | %(funcName)s | %(lineno)d | %(message)s')
    self.file_handler.setFormatter(formatter)
    self.stream_handler.setFormatter(formatter)

    # Create logger and add handlers
    self.logger = logging.getLogger("unittest")
    self.logger.setLevel(logging.DEBUG)
    self.logger.addHandler(self.file_handler)
    self.logger.addHandler(self.stream_handler)
    self.logger.debug("Logger is set up")
     
    # Start serial communication to low-level board
    self.si = comm.SerialInterface()
    self.si.start() # Displays an error if port not found (not running on Pandaboard)
    self.logger.info("Serial interface set up")

    # Build Queue objects for IPC. Name shows producer_consumer.
    self.qNav_loc = Queue()
    self.qMove_nav = Queue()
    self.logger.debug("Queue objects created")

    # Get map, waypoints and map properties
    self.course_map = mapper.unpickle_map(path_to_qwe + "mapping/map.pkl")
    self.logger.info("Map unpickled")
    self.waypoints = mapper.unpickle_waypoints(path_to_qwe + "mapping/waypoints.pkl")
    self.logger.info("Waypoints unpickled")

    # Find start location
    self.start_x = self.waypoints["start"][0][0] * float(nav.env_config["cellsize"]) * 39.3701
    self.start_y = self.waypoints["start"][0][1] * float(nav.env_config["cellsize"]) * 39.3701
    self.start_theta = 0

    # Build shared data structures
    self.manager = Manager()
    self.bot_loc = self.manager.dict(x=self.start_x, y=self.start_y, theta=self.start_theta)
    self.bot_state = self.manager.dict(nav_type=None, action_type=None)
    self.logger.debug("Shared data structures created")

    # Start nav process
    self.scNav = comm.SerialCommand(self.si.commands, self.si.responses)
    self.pNav = Process(target=nav.run, args=(self.bot_loc, self.course_map, self.waypoints, self.qNav_loc, self.scNav, \
      self.bot_state, self.qMove_nav, self.logger))
    self.pNav.start()
    self.logger.info("Navigator process started")

  def tearDown(self):
    """Close serial interface threads"""

    # Join nav process
    self.pNav.join() 
    self.logger.info("Joined navigation process")

    # Join serial interface process
    self.scNav.quit()
    self.si.join()
    self.logger.info("Joined serial interface process")

    # Remove loggers. Not doing this results in the same log entry being written many times.
    self.logger.removeHandler(self.file_handler)
    self.logger.removeHandler(self.stream_handler)

  def test_start_at_goal(self):
    """Pass in a goal pose that's the same as the start pose"""
    # Build goal pose that's the same as the start pose
    goal_pose = nav.macro_move(self.start_x, self.start_y, self.start_theta, datetime.now())
    self.logger.debug("Created goal pose {}".format(pp.pformat(goal_pose)))

    # Send goal pose via queue
    self.logger.debug("About to send goal pose to queue with ID {}".format(str(self.qMove_nav)))
    self.qMove_nav.put(goal_pose)
    self.logger.debug("Put goal pose into queue")

    # Pass a die command to nav
    self.logger.info("Telling nav to die")
    self.qMove_nav.put("die")

  def test_start_nearly_at_goal(self):
    """Pass in a goal pose that's nearly the same as the start pose"""
    # Build goal pose that's the same as the start pose
    goal_pose = nav.macro_move(self.start_x + .05, self.start_y + .05, self.start_theta, datetime.now())
    self.logger.debug("Created goal pose {}".format(pp.pformat(goal_pose)))

    # Send goal pose via queue
    self.logger.debug("About to send goal pose to queue with ID {}".format(str(self.qMove_nav)))
    self.qMove_nav.put(goal_pose)
    self.logger.debug("Put goal pose into queue")

    # Pass a die command to nav
    self.logger.info("Telling nav to die")
    self.qMove_nav.put("die")

  def test_simple_XY_move(self):
    """Pass in a goal pose that only differes on the XY plane from the start pose"""
    # Build goal pose that's the same as the start pose
    goal_pose = nav.macro_move(self.start_x + 5, self.start_y + 5, self.start_theta, datetime.now())
    self.logger.debug("Created goal pose {}".format(pp.pformat(goal_pose)))

    # Send goal pose via queue
    self.logger.debug("About to send goal pose to queue with ID {}".format(str(self.qMove_nav)))
    self.qMove_nav.put(goal_pose)
    self.logger.debug("Put goal pose into queue")

    # Pass a die command to nav
    self.logger.info("Telling nav to die")
    self.qMove_nav.put("die")

  #@unittest.skip("Not ready")
  def test_simple_theta_move(self):
    """Pass in a goal pose that's the same as the start pose"""
    # Build goal pose that's the same as the start pose
    goal_pose = nav.macro_move(self.start_x, self.start_y, self.start_theta + 2, datetime.now())
    self.logger.debug("Created goal pose {}".format(pp.pformat(goal_pose)))

    # Send goal pose via queue
    self.logger.debug("About to send goal pose to queue with ID {}".format(str(self.qMove_nav)))
    self.qMove_nav.put(goal_pose)
    self.logger.debug("Put goal pose into queue")

    # Pass a die command to nav
    self.logger.info("Telling nav to die")
    self.qMove_nav.put("die")

  def test_two_moves(self):
    """Pass in a goal pose that's the same as the start pose"""
    # Build goal pose that's the same as the start pose
    goal_pose = nav.macro_move(self.start_x + 5, self.start_y + 5, self.start_theta + 2, datetime.now())
    self.logger.debug("Created goal pose {}".format(pp.pformat(goal_pose)))

    # Send goal pose via queue
    self.logger.debug("About to send goal pose to queue with ID {}".format(str(self.qMove_nav)))
    self.qMove_nav.put(goal_pose)
    self.logger.debug("Put goal pose into queue")

    goal_pose = nav.macro_move(self.start_x + 6, self.start_y + 2, self.start_theta, datetime.now())
    self.logger.debug("Created goal pose {}".format(pp.pformat(goal_pose)))

    # Send goal pose via queue
    self.logger.debug("About to send goal pose to queue with ID {}".format(str(self.qMove_nav)))
    self.qMove_nav.put(goal_pose)
    self.logger.debug("Put goal pose into queue")

    # Pass a die command to nav
    self.logger.info("Telling nav to die")
    self.qMove_nav.put("die")


class TestlocsEqual(unittest.TestCase):

  def setUp(self):
    """Create nav object and feed it appropriate data"""

    # Create file and stream handlers
    self.file_handler = logging.handlers.RotatingFileHandler(path_to_qwe + "logs/unittests.log", maxBytes=512000, backupCount=50)
    self.file_handler.setLevel(logging.DEBUG)
    self.stream_handler = logging.StreamHandler()
    self.stream_handler.setLevel(logging.WARN)

    # Create formatter and add to handlers
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(filename)s | %(funcName)s | %(lineno)d | %(message)s')
    self.file_handler.setFormatter(formatter)
    self.stream_handler.setFormatter(formatter)

    # Create logger and add handlers
    self.logger = logging.getLogger("unittest")
    self.logger.setLevel(logging.DEBUG)
    self.logger.addHandler(self.file_handler)
    self.logger.addHandler(self.stream_handler)
    self.logger.debug("Logger is set up")
     
    # Start serial communication to low-level board
    self.si = comm.SerialInterface()
    self.si.start() # Displays an error if port not found (not running on Pandaboard)
    self.logger.info("Serial interface set up")

    # Build Queue objects for IPC. Name shows producer_consumer.
    self.qNav_loc = Queue()
    self.qMove_nav = Queue()
    self.logger.debug("Queue objects created")

    # Get map, waypoints and map properties
    self.course_map = mapper.unpickle_map(path_to_qwe + "mapping/map.pkl")
    self.logger.info("Map unpickled")
    self.waypoints = mapper.unpickle_waypoints(path_to_qwe + "mapping/waypoints.pkl")
    self.logger.info("Waypoints unpickled")

    # Build shared data structures
    self.manager = Manager()
    self.start_x = self.waypoints["start"][0][0] * float(nav.env_config["cellsize"]) * 39.3701
    self.start_y = self.waypoints["start"][0][1] * float(nav.env_config["cellsize"]) * 39.3701
    self.start_theta = 0
    self.bot_loc = self.manager.dict(x=self.start_x, y=self.start_y, theta=self.start_theta)
    self.bot_state = self.manager.dict(nav_type=None, action_type=None)
    self.logger.debug("Shared data structures created")

    # Build nav object
    self.scNav = comm.SerialCommand(self.si.commands, self.si.responses)
    self.Nav = nav.Nav(self.bot_loc, self.course_map, self.waypoints, self.qNav_loc, self.scNav, self.bot_state, self.qMove_nav, \
      self.logger)
    self.logger.info("Nav object instantiated")

  def tearDown(self):
    """Close serial interface threads"""

    self.logger.removeHandler(self.file_handler)
    self.logger.removeHandler(self.stream_handler)

    self.scNav.quit()
    self.si.join()

    # Create formatter and add to handlers
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(filename)s | %(funcName)s | %(lineno)d | %(message)s')

  def test_locsEqual_default_config_mixed_sign_twice_error(self):
    """Test function that's to check if two poses are equal to within some error. This test uses twice the acceptable error and
    mixed negitive and positve values"""

    # Translate bot_loc data into internal units
    x0 = nav.config["XYErr"]
    y0 = nav.config["XYErr"]
    theta0 = nav.config["thetaErr"]

    # Create a second pose that's off by twice of the acceptable error
    x1 = nav.config["XYErr"] * -1
    y1 = nav.config["XYErr"] * -1
    theta1 = nav.config["thetaErr"] * -1

    self.logger.info("Testing locsEqual with {} {} {} and {} {} {}".format(x0, y0, theta0, x1, y1, theta1))

    result = self.Nav.locsEqual(x0, y0, theta0, x1, y1, theta1)

    self.logger.debug("locsEqual returned {}".format(result))

    self.assertFalse(result, "locsEqual returned True with mixed sign values and diff of twice the acceptable error")

  def test_locsEqual_default_config_mixed_sign_half_error(self):
    """Test function that's to check if two poses are equal to within some error. This test uses half the acceptable error and
    mixed negitive and positve values"""

    # Translate bot_loc data into internal units
    x0 = nav.config["XYErr"] / 4
    y0 = nav.config["XYErr"] / 4
    theta0 = nav.config["thetaErr"] / 4

    # Create a second pose that's off by half of the acceptable error
    x1 = nav.config["XYErr"] / -4
    y1 = nav.config["XYErr"] / -4
    theta1 = nav.config["thetaErr"] / -4

    self.logger.info("Testing locsEqual with {} {} {} and {} {} {}".format(x0, y0, theta0, x1, y1, theta1))

    result = self.Nav.locsEqual(x0, y0, theta0, x1, y1, theta1)

    self.logger.debug("locsEqual returned {}".format(result))

    self.assertTrue(result, "locsEqual returned False with mixed sign values and diff of half the acceptable error")

  def test_locsEqual_default_config_neg_vals_half_error(self):
    """Test function that's to check if two poses are equal to within some error. This test uses half the acceptable error and
    negitve values"""

    # Translate bot_loc data into internal units
    x0 = self.Nav.XYFrombot_locUC(self.bot_loc["x"]) * -1
    y0 = self.Nav.XYFrombot_locUC(self.bot_loc["y"]) * -1
    theta0 = self.Nav.thetaFrombot_locUC(self.bot_loc["theta"]) * -1

    # Create a second pose that's off by half of the acceptable error
    x1 = x0 + nav.config["XYErr"] / -2
    y1 = y0 + nav.config["XYErr"] / -2
    theta1 = theta0 + nav.config["thetaErr"] / -2

    self.logger.info("Testing locsEqual with {} {} {} and {} {} {}".format(x0, y0, theta0, x1, y1, theta1))

    result = self.Nav.locsEqual(x0, y0, theta0, x1, y1, theta1)

    self.logger.debug("locsEqual returned {}".format(result))

    self.assertTrue(result, "locsEqual returned False with negitive values and diff of half the acceptable error")

  def test_locsEqual_default_config_neg_vals_twice_error(self):
    """Test function that's to check if two poses are equal to within some error. This test uses twice the acceptable error and
    negitve values"""

    # Translate bot_loc data into internal units
    x0 = self.Nav.XYFrombot_locUC(self.bot_loc["x"]) * -1
    y0 = self.Nav.XYFrombot_locUC(self.bot_loc["y"]) * -1
    theta0 = self.Nav.thetaFrombot_locUC(self.bot_loc["theta"]) * -1

    # Create a second pose that's off by twice the acceptable error
    x1 = x0 + nav.config["XYErr"] * -2
    y1 = y0 + nav.config["XYErr"] * -2
    theta1 = theta0 + nav.config["thetaErr"] * -2

    self.logger.info("Testing locsEqual with {} {} {} and {} {} {}".format(x0, y0, theta0, x1, y1, theta1))

    result = self.Nav.locsEqual(x0, y0, theta0, x1, y1, theta1)

    self.logger.debug("locsEqual returned {}".format(result))

    self.assertFalse(result, "locsEqual returned True with negitive values and with diff twice of acceptable error")

  def test_locsEqual_default_config_neg_vals_0_error(self):
    """Test function that's to check if two poses are equal to within some error. This test uses zero error and negitive values."""

    self.logger.info("Testing locsEqual with {} {} {} and {} {} {}".format(-1, -.5, -.25, -1, -.5, -.25))

    result = self.Nav.locsEqual(-1, -.5, -.25, -1, -.5, -.25)

    self.logger.debug("locsEqual returned {}".format(result))

    self.assertTrue(result, "locsEqual returned False with negitve values and zero error")

  def test_locsEqual_default_config_0_vals(self):
    """Test function that's to check if two poses are equal to within some error. This test uses zero for all values."""

    self.logger.info("Testing locsEqual with {} {} {} and {} {} {}".format(0, 0, 0, 0, 0, 0))

    result = self.Nav.locsEqual(0, 0, 0, 0, 0, 0)

    self.logger.debug("locsEqual returned {}".format(result))

    self.assertTrue(result, "locsEqual returned False with all-zero inputs")

  def test_locsEqual_default_config_0_error(self):
    """Test function that's to check if two poses are equal to within some error. This test uses zero error."""

    # Translate bot_loc data into internal units
    x0 = self.Nav.XYFrombot_locUC(self.bot_loc["x"])
    y0 = self.Nav.XYFrombot_locUC(self.bot_loc["y"])
    theta0 = self.Nav.thetaFrombot_locUC(self.bot_loc["theta"])

    self.logger.info("Testing locsEqual with {} {} {} and {} {} {}".format(x0, y0, theta0, x0, y0, theta0))

    result = self.Nav.locsEqual(x0, y0, theta0, x0, y0, theta0)

    self.logger.debug("locsEqual returned {}".format(result))

    self.assertTrue(result, "locsEqual returned False when diff 0")

  def test_locsEqual_default_config_twice_error(self):
    """Test function that's to check if two poses are equal to within some error. This test uses twice the acceptable error."""

    # Translate bot_loc data into internal units
    x0 = self.Nav.XYFrombot_locUC(self.bot_loc["x"])
    y0 = self.Nav.XYFrombot_locUC(self.bot_loc["y"])
    theta0 = self.Nav.thetaFrombot_locUC(self.bot_loc["theta"])

    # Create a second pose that's off by half of the acceptable error
    x1 = x0 + nav.config["XYErr"] * 2
    y1 = y0 + nav.config["XYErr"] * 2
    theta1 = theta0 + nav.config["thetaErr"] * 2

    self.logger.info("Testing locsEqual with {} {} {} and {} {} {}".format(x0, y0, theta0, x1, y1, theta1))

    result = self.Nav.locsEqual(x0, y0, theta0, x1, y1, theta1)

    self.logger.debug("locsEqual returned {}".format(result))

    self.assertFalse(result, "locsEqual returned True when diff was twice of acceptable error")

  def test_locsEqual_default_config_half_error(self):
    """Test function that's to check if two poses are equal to within some error. This test uses half the acceptable error."""

    # Translate bot_loc data into internal units
    x0 = self.Nav.XYFrombot_locUC(self.bot_loc["x"])
    y0 = self.Nav.XYFrombot_locUC(self.bot_loc["y"])
    theta0 = self.Nav.thetaFrombot_locUC(self.bot_loc["theta"])

    # Create a second pose that's off by half of the acceptable error
    x1 = x0 + nav.config["XYErr"]/2
    y1 = y0 + nav.config["XYErr"]/2
    theta1 = theta0 + nav.config["thetaErr"]/2

    self.logger.info("Testing locsEqual with {} {} {} and {} {} {}".format(x0, y0, theta0, x1, y1, theta1))

    result = self.Nav.locsEqual(x0, y0, theta0, x1, y1, theta1)

    self.logger.debug("locsEqual returned {}".format(result))

    self.assertTrue(result, "locsEqual returned False when diff was half of acceptable error")

class TestwhichXYTheta(unittest.TestCase):

  def setUp(self):
    """Create nav object and feed it appropriate data"""
    
    # Create file and stream handlers
    self.file_handler = logging.handlers.RotatingFileHandler(path_to_qwe + "logs/unittests.log", maxBytes=512000, backupCount=50)
    self.file_handler.setLevel(logging.DEBUG)
    self.stream_handler = logging.StreamHandler()
    self.stream_handler.setLevel(logging.WARN)

    # Create formatter and add to handlers
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(filename)s | %(funcName)s | %(lineno)d | %(message)s')
    self.file_handler.setFormatter(formatter)
    self.stream_handler.setFormatter(formatter)

    # Create logger and add handlers
    self.logger = logging.getLogger("unittest")
    self.logger.setLevel(logging.DEBUG)
    self.logger.addHandler(self.file_handler)
    self.logger.addHandler(self.stream_handler)
    self.logger.debug("Logger is set up")
     
    # Start serial communication to low-level board
    self.si = comm.SerialInterface()
    self.si.start() # Displays an error if port not found (not running on Pandaboard)
    self.logger.info("Serial interface set up")

    # Build shared data structures
    self.manager = Manager()
    self.bot_loc = self.manager.dict(x=1, y=1, theta=0) # Same params used in the env1.txt example file
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
    self.scNav = comm.SerialCommand(self.si.commands, self.si.responses)
    self.Nav = nav.Nav(self.bot_loc, self.course_map, self.waypoints, self.qNav_loc, self.scNav, self.bot_state, self.qMove_nav, \
      self.logger)
    self.logger.info("Nav object instantiated")

  def tearDown(self):
    """Close serial interface threads"""

    self.logger.removeHandler(self.file_handler)
    self.logger.removeHandler(self.stream_handler)

    self.scNav.quit()
    self.si.join()

  def test_whichXYTheta_x_change(self):
    """Test helper function that finds if movement is to be in the XY plane or the theta dimension. This test checks steps with
    a difference in x value."""

    sol = [{'cont_theta': 0.000,
    'cont_x': 3.350,
    'cont_y': 3.250,
    'theta': 0,
    'x': 33,
    'y': 32},
    {'cont_theta': 0.000,
    'cont_x': 3.250,
    'cont_y': 3.250,
    'theta': 0,
    'x': 32,
    'y': 32}]

    self.logger.debug("Testing whichXYTheta with sol: " + pp.pformat(sol))

    result = self.Nav.whichXYTheta(sol[0], sol[1])

    self.logger.info("whichXYTheta returned: {}".format(result))

    self.assertEqual(result, "xy", "Expected \"xy\" but received {}".format(result))

  def test_whichXYTheta_y_change(self):
    """Test helper function that finds if movement is to be in the XY plane or the theta dimension. This test checks steps a 
    difference in y value."""

    sol = [{'cont_theta': 0.000,
    'cont_x': 3.250,
    'cont_y': 3.250,
    'theta': 0,
    'x': 32,
    'y': 32},
    {'cont_theta': 0.000,
    'cont_x': 3.250,
    'cont_y': 4.250,
    'theta': 0,
    'x': 32,
    'y': 40}]

    self.logger.debug("Testing whichXYTheta with sol: " + pp.pformat(sol))

    result = self.Nav.whichXYTheta(sol[0], sol[1])

    self.logger.info("whichXYTheta returned: {}".format(result))

    self.assertEqual(result, "xy", "Expected \"xy\" but received {}".format(result))

  def test_whichXYTheta_theta_change(self):
    """Test helper function that finds if movement is to be in the XY plane or the theta dimension. This test checks steps with a
    change in the theta value."""

    sol = [{'cont_theta': 0.393,
    'cont_x': 2.450,
    'cont_y': 1.750,
    'theta': 1,
    'x': 24,
    'y': 17},
    {'cont_theta': 0.785,
    'cont_x': 2.450,
    'cont_y': 1.750,
    'theta': 2,
    'x': 24,
    'y': 17}]

    self.logger.debug("Testing whichXYTheta with sol: " + pp.pformat(sol))

    result = self.Nav.whichXYTheta(sol[0], sol[1])

    self.logger.info("whichXYTheta returned: {}".format(result))

    self.assertEqual(result, "theta", "Expected \"theta\" but received {}".format(result))

  def test_whichXYTheta_x_y_change(self):
    """Test helper function that finds if movement is to be in the XY plane or the theta dimension. This test checks changes in
    x, y and theta."""

    sol = [{'cont_theta': '0.3926991',
    'cont_x': '0.2762250',
    'cont_y': '0.2254250',
    'theta': '1',
    'x': '43',
    'y': '35'},
    {'cont_theta': '0.3926991',
    'cont_x': '0.3143250',
    'cont_y': '0.2444750',
    'theta': '1',
    'x': '49',
    'y': '38'}]

    self.logger.debug("Testing whichXYTheta with sol: " + pp.pformat(sol))

    result = self.Nav.whichXYTheta(sol[0], sol[1])

    self.logger.info("whichXYTheta returned: {}".format(result))

    self.assertEqual(result, "xy", "Expected \"xy\" but received {}".format(result))

  def test_whichXYTheta_x_theta_change(self):
    """Test helper function that finds if movement is to be in the XY plane or the theta dimension. This test checks changes in x
    and theta."""

    sol = [{'cont_theta': '0.0000000',
    'cont_x': '0.2762250',
    'cont_y': '0.2762250',
    'theta': '0',
    'x': '43',
    'y': '43'},
    {'cont_theta': '0.3926991',
    'cont_x': '0.3143250',
    'cont_y': '0.2762250',
    'theta': '1',
    'x': '49',
    'y': '43'}]

    self.logger.debug("Testing whichXYTheta with sol: " + pp.pformat(sol))

    result = self.Nav.whichXYTheta(sol[0], sol[1])

    self.logger.info("whichXYTheta returned: {}".format(result))

    self.assertEqual(result, nav.errors["ERROR_ARCS_DISALLOWED"], 
      "Expected {} but received {}".format(nav.errors["ERROR_ARCS_DISALLOWED"], result))

  def test_whichXYTheta_y_theta_change(self):
    """Test helper function that finds if movement is to be in the XY plane or the theta dimension. This test checks changes in y
    and theta."""

    sol = [{'cont_theta': '0.0000000',
    'cont_x': '0.2762250',
    'cont_y': '0.2762250',
    'theta': '0',
    'x': '43',
    'y': '43'},
    {'cont_theta': '0.3926991',
    'cont_x': '0.2762250',
    'cont_y': '0.2063750',
    'theta': '1',
    'x': '43',
    'y': '32'}]

    self.logger.debug("Testing whichXYTheta with sol: " + pp.pformat(sol))

    result = self.Nav.whichXYTheta(sol[0], sol[1])

    self.logger.info("whichXYTheta returned: {}".format(result))

    self.assertEqual(result, nav.errors["ERROR_ARCS_DISALLOWED"], 
      "Expected {} but received {}".format(nav.errors["ERROR_ARCS_DISALLOWED"], result))

  def test_whichXYTheta_x_y_theta_change(self):
    """Test helper function that finds if movement is to be in the XY plane or the theta dimension. This test checks changes in
    x, y and theta."""

    sol = [{'cont_theta': '0.0000000',
    'cont_x': '0.2762250',
    'cont_y': '0.2762250',
    'theta': '0',
    'x': '43',
    'y': '43'},
    {'cont_theta': '0.3926991',
    'cont_x': '0.3143250',
    'cont_y': '0.2063750',
    'theta': '1',
    'x': '49',
    'y': '32'}]

    self.logger.debug("Testing whichXYTheta with sol: " + pp.pformat(sol))

    result = self.Nav.whichXYTheta(sol[0], sol[1])

    self.logger.info("whichXYTheta returned: {}".format(result))

    self.assertEqual(result, nav.errors["ERROR_ARCS_DISALLOWED"], 
      "Expected {} but received {}".format(nav.errors["ERROR_ARCS_DISALLOWED"], result))

  def test_whichXYTheta_no_change(self):
    """Test helper function that finds if movement is to be in the XY plane or the theta dimension. This test checks steps with
    no previous move and no difference in any attribute."""

    sol = [{'cont_theta': 0.000,
    'cont_x': 3.350,
    'cont_y': 3.250,
    'theta': 0,
    'x': 33,
    'y': 32},
    {'cont_theta': 0.000,
    'cont_x': 3.350,
    'cont_y': 3.250,
    'theta': 0,
    'x': 33,
    'y': 32}]

    self.logger.debug("Testing whichXYTheta with sol: " + pp.pformat(sol))

    result = self.Nav.whichXYTheta(sol[0], sol[1])

    self.logger.info("whichXYTheta returned: {}".format(result))

    self.assertEqual(result, nav.errors["ERROR_NO_CHANGE"], "Expected {} but received \
      {}".format(nav.errors["ERROR_NO_CHANGE"], result))

if __name__ == "__main__":
  unittest.main() # Execute all tests
