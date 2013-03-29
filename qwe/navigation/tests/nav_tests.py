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
    formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')
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
    start_x = self.waypoints["start"][0][0] * float(nav.env_config["cellsize"])
    start_y = self.waypoints["start"][0][1] * float(nav.env_config["cellsize"])
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
    formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')
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
    self.start_x = self.waypoints["start"][0][0] * float(nav.env_config["cellsize"])
    self.start_y = self.waypoints["start"][0][1] * float(nav.env_config["cellsize"])
    self.start_theta = 0
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

    self.logger.removeHandler(self.file_handler)
    self.logger.removeHandler(self.stream_handler)

    self.scNav.quit()
    self.si.join()
    self.pNav.join()
    self.logger.info("Joined navigation process")

  @unittest.skip("Hangs while attempting to put item in queue")
  def test_start_at_goal(self):
    """Pass in a goal pose that's the same as the start pose"""

    # Build goal pose that's the same as the start pose
    goal_pose = nav.macro_move(self.start_x, self.start_y, self.start_theta, datetime.now())
    self.logger.debug("Created goal pose: " + pp.pformat(goal_pose))

    # Send goal pose to nav via queue
    self.logger.debug("Putting into queue")
    self.logger.debug("Queue ID: " + pp.pformat(self.qMove_nav))
    self.logger.debug("Queue size: " + pp.pformat(self.Move_nav.qsize()))
    qMove_nav.put(goal_pose)
    self.logger.debug("Goal pose put in queue")


class TestSimpleHelpers(unittest.TestCase):

  def setUp(self):
    """Create nav object and feed it appropriate data"""

    # Create file and stream handlers
    self.file_handler = logging.handlers.RotatingFileHandler(path_to_qwe + "logs/unittests.log", maxBytes=512000, backupCount=50)
    self.file_handler.setLevel(logging.DEBUG)
    self.stream_handler = logging.StreamHandler()
    self.stream_handler.setLevel(logging.WARN)

    # Create formatter and add to handlers
    formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')
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
    self.start_x = self.waypoints["start"][0][0] * float(nav.env_config["cellsize"])
    self.start_y = self.waypoints["start"][0][1] * float(nav.env_config["cellsize"])
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
    formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')

  def test_atGoal_exact(self):
    """Test function that checks if a goal pose is the same as the bot's current location. Use goal pose that's exactly the bot's
    current location"""

    goal_x = self.start_x
    goal_y = self.start_y
    goal_theta = self.start_theta

    self.logger.info("Testing atGoal with goal {} {} {} and position {} {} {}".format(goal_x, goal_y, goal_theta, self.start_x, \
      self.start_y, self.start_theta))

    result = self.Nav.atGoal(goal_x, goal_y, goal_theta)

    self.logger.debug("atGoal returned {}".format(str(result)))

    self.assertTrue(result, "atGoal returned False when exactly at goal")

  def test_atGoal_3_sig_figs_off_3(self):
    """Test function that checks if a goal pose is the same as the bot's current location. Use goal pose that's off by 3 sig figs
    and accept a tolerance of 3 sig figs."""

    goal_x = self.start_x + .001
    goal_y = self.start_y + .001
    goal_theta = self.start_theta + .001

    self.logger.info("Testing atGoal with goal {} {} {} and position {} {} {}".format(goal_x, goal_y, goal_theta, self.start_x, \
      self.start_y, self.start_theta))

    result = self.Nav.atGoal(goal_x, goal_y, goal_theta, sig_figs=3)

    self.logger.debug("atGoal returned {}".format(str(result)))

    self.assertTrue(result, "atGoal returned False when 3 sig figs from goal and sig_figs=3")

  def test_atGoal_4_sig_figs_off_3(self):
    """Test function that checks if a goal pose is the same as the bot's current location. Use goal pose that's off by 3 sig figs
    and accept a tolerance of 4 sig figs."""

    goal_x = self.start_x + .001
    goal_y = self.start_y + .001
    goal_theta = self.start_theta + .001

    self.logger.info("Testing atGoal with goal {} {} {} and position {} {} {}".format(goal_x, goal_y, goal_theta, self.start_x, \
      self.start_y, self.start_theta))

    result = self.Nav.atGoal(goal_x, goal_y, goal_theta, sig_figs=4)

    self.logger.debug("atGoal returned {}".format(str(result)))

    self.assertFalse(result, "atGoal returned True when 3 sig figs from goal and sig_figs=4")

class TestXYxorTheta(unittest.TestCase):

  def setUp(self):
    """Create nav object and feed it appropriate data"""
    
    # Create file and stream handlers
    self.file_handler = logging.handlers.RotatingFileHandler(path_to_qwe + "logs/unittests.log", maxBytes=512000, backupCount=50)
    self.file_handler.setLevel(logging.DEBUG)
    self.stream_handler = logging.StreamHandler()
    self.stream_handler.setLevel(logging.WARN)

    # Create formatter and add to handlers
    formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')
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

  def test_XYxorTheta_x_change(self):
    """Test helper function that checks if the previous and current steps changed in the XY plane or the theta dimension, but not
    both. This test checks steps with changes in x only."""


    sol = [{'cont_theta': '0.000',
    'cont_x': '3.350',
    'cont_y': '3.250',
    'theta': '0',
    'x': '33',
    'y': '32'},
    {'cont_theta': '0.000',
    'cont_x': '3.250',
    'cont_y': '3.250',
    'theta': '0',
    'x': '32',
    'y': '32'}]

    self.logger.debug("Testing XYxorTheta with sol: " + pp.pformat(sol))

    result = self.Nav.XYxorTheta(sol[0], sol[1])

    self.logger.info("XYxorTheta returned: {}".format(result))

    self.assertTrue(result, "Expected True but received {}".format(result))

  def test_XYxorTheta_y_change(self):
    """Test helper function that checks if the previous and current steps changed in the XY plane or the theta dimension, but not
    both. This test checks steps with changes in y only."""


    sol = [{'cont_theta': '0.000',
    'cont_x': '3.250',
    'cont_y': '3.250',
    'theta': '0',
    'x': '32',
    'y': '32'},
    {'cont_theta': '0.000',
    'cont_x': '3.250',
    'cont_y': '4.250',
    'theta': '0',
    'x': '32',
    'y': '40'}]

    self.logger.debug("Testing XYxorTheta with sol: " + pp.pformat(sol))

    result = self.Nav.XYxorTheta(sol[0], sol[1])

    self.logger.info("XYxorTheta returned: {}".format(result))

    self.assertTrue(result, "Expected True but received {}".format(result))

  def test_XYxorTheta_theta_change(self):
    """Test helper function that checks if the previous and current steps changed in the XY plane or the theta dimension, but not
    both. This test checks steps with changes in theta only."""


    sol = [{'cont_theta': '0.393',
    'cont_x': '2.450',
    'cont_y': '1.750',
    'theta': '1',
    'x': '24',
    'y': '17'},
    {'cont_theta': '0.785',
    'cont_x': '2.450',
    'cont_y': '1.750',
    'theta': '2',
    'x': '24',
    'y': '17'}]

    self.logger.debug("Testing XYxorTheta with sol: " + pp.pformat(sol))

    result = self.Nav.XYxorTheta(sol[0], sol[1])

    self.logger.info("XYxorTheta returned: {}".format(result))

    self.assertTrue(result, "Expected True but received {}".format(result))

  def test_XYxorTheta_x_and_theta_change(self):
    """Test helper function that checks if the previous and current steps changed in the XY plane or the theta dimension, but not
    both. This test checks steps with changes in x and theta."""


    sol = [{'cont_theta': '0.393',
    'cont_x': '3.250',
    'cont_y': '1.750',
    'theta': '1',
    'x': '32',
    'y': '17'},
    {'cont_theta': '0.785',
    'cont_x': '2.450',
    'cont_y': '1.750',
    'theta': '2',
    'x': '24',
    'y': '17'}]

    self.logger.debug("Testing XYxorTheta with sol: " + pp.pformat(sol))

    result = self.Nav.XYxorTheta(sol[0], sol[1])

    self.logger.info("XYxorTheta returned: {}".format(result))

    self.assertFalse(result, "Expected False but received {}".format(result))

  def test_XYxorTheta_y_and_theta_change(self):
    """Test helper function that checks if the previous and current steps changed in the XY plane or the theta dimension, but not
    both. This test checks steps with changes in y and theta."""


    sol = [{'cont_theta': '0.393',
    'cont_x': '3.250',
    'cont_y': '1.750',
    'theta': '1',
    'x': '32',
    'y': '17'},
    {'cont_theta': '0.785',
    'cont_x': '3.250',
    'cont_y': '4.250',
    'theta': '2',
    'x': '32',
    'y': '40'}]

    self.logger.debug("Testing XYxorTheta with sol: " + pp.pformat(sol))

    result = self.Nav.XYxorTheta(sol[0], sol[1])

    self.logger.info("XYxorTheta returned: {}".format(result))

    self.assertFalse(result, "Expected False but received {}".format(result))

  def test_XYxorTheta_x_and_y_change(self):
    """Test helper function that checks if the previous and current steps changed in the XY plane or the theta dimension, but not
    both. This test checks steps with changes in x and y."""


    sol = [{'cont_theta': '0.393',
    'cont_x': '3.250',
    'cont_y': '1.750',
    'theta': '1',
    'x': '32',
    'y': '17'},
    {'cont_theta': '0.393',
    'cont_x': '2.450',
    'cont_y': '4.250',
    'theta': '1',
    'x': '24',
    'y': '40'}]

    self.logger.debug("Testing XYxorTheta with sol: " + pp.pformat(sol))

    result = self.Nav.XYxorTheta(sol[0], sol[1])

    self.logger.info("XYxorTheta returned: {}".format(result))

    self.assertTrue(result, "Expected False but received {}".format(result))

  def test_XYxorTheta_x_and_y_and_theta_change(self):
    """Test helper function that checks if the previous and current steps changed in the XY plane or the theta dimension, but not
    both. This test checks steps with changes in x, y and theta."""


    sol = [{'cont_theta': '0.392',
    'cont_x': '3.250',
    'cont_y': '1.750',
    'theta': '1',
    'x': '32',
    'y': '17'},
    {'cont_theta': '0.393',
    'cont_x': '2.450',
    'cont_y': '4.250',
    'theta': '2',
    'x': '24',
    'y': '40'}]

    self.logger.debug("Testing XYxorTheta with sol: " + pp.pformat(sol))

    result = self.Nav.XYxorTheta(sol[0], sol[1])

    self.logger.info("XYxorTheta returned: {}".format(result))

    self.assertFalse(result, "Expected False but received {}".format(result))

  def test_XYxorTheta_no_change(self):
    """Test helper function that checks if the previous and current steps changed in the XY plane or the theta dimension, but not
    both. This test checks steps with no change in any attribute"""

    sol = [{'cont_theta': '0.000',
    'cont_x': '3.350',
    'cont_y': '3.250',
    'theta': '0',
    'x': '33',
    'y': '32'},
    {'cont_theta': '0.000',
    'cont_x': '3.350',
    'cont_y': '3.250',
    'theta': '0',
    'x': '33',
    'y': '32'}]

    self.logger.debug("Testing XYxorTheta with sol: " + pp.pformat(sol))

    result = self.Nav.XYxorTheta(sol[0], sol[1])

    self.logger.info("XYxorTheta returned: {}".format(result))

    self.assertEqual(result, nav.errors["ERROR_NO_CHANGE"], "Expected {} but received \
      {}".format(nav.errors["ERROR_NO_CHANGE"], result))

class TestWhichXYTheta(unittest.TestCase):

  def setUp(self):
    """Create nav object and feed it appropriate data"""
    
    # Create file and stream handlers
    self.file_handler = logging.handlers.RotatingFileHandler(path_to_qwe + "logs/unittests.log", maxBytes=512000, backupCount=50)
    self.file_handler.setLevel(logging.DEBUG)
    self.stream_handler = logging.StreamHandler()
    self.stream_handler.setLevel(logging.WARN)

    # Create formatter and add to handlers
    formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')
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


  def test_whichXYTheta_x_change_first_move(self):
    """Test helper function that finds if movement is to be in the XY plane or the theta dimension. This test checks steps with
    no previous move a difference in x value."""

    sol = [{'cont_theta': '0.000',
    'cont_x': '3.350',
    'cont_y': '3.250',
    'theta': '0',
    'x': '33',
    'y': '32'},
    {'cont_theta': '0.000',
    'cont_x': '3.250',
    'cont_y': '3.250',
    'theta': '0',
    'x': '32',
    'y': '32'}]

    self.logger.debug("Testing whichXYTheta with sol: " + pp.pformat(sol))

    result = self.Nav.whichXYTheta(sol[0], sol[1])

    self.logger.info("whichXYTheta returned: {}".format(result))

    self.assertEqual(result, "xy", "Expected \"x\" but received {}".format(result))

  def test_whichXYTheta_y_change_first_move(self):
    """Test helper function that finds if movement is to be in the XY plane or the theta dimension. This test checks steps with
    no previous move a difference in y value."""

    sol = [{'cont_theta': '0.000',
    'cont_x': '3.250',
    'cont_y': '3.250',
    'theta': '0',
    'x': '32',
    'y': '32'},
    {'cont_theta': '0.000',
    'cont_x': '3.250',
    'cont_y': '4.250',
    'theta': '0',
    'x': '32',
    'y': '40'}]

    self.logger.debug("Testing whichXYTheta with sol: " + pp.pformat(sol))

    result = self.Nav.whichXYTheta(sol[0], sol[1])

    self.logger.info("whichXYTheta returned: {}".format(result))

    self.assertEqual(result, "xy", "Expected \"y\" but received {}".format(result))

  def test_whichXYTheta_theta_change_first_move(self):
    """Test helper function that finds if movement is to be in the XY plane or the theta dimension. This test checks steps with
    no previous move a difference in theta value."""

    sol = [{'cont_theta': '0.393',
    'cont_x': '2.450',
    'cont_y': '1.750',
    'theta': '1',
    'x': '24',
    'y': '17'},
    {'cont_theta': '0.785',
    'cont_x': '2.450',
    'cont_y': '1.750',
    'theta': '2',
    'x': '24',
    'y': '17'}]

    self.logger.debug("Testing whichXYTheta with sol: " + pp.pformat(sol))

    result = self.Nav.whichXYTheta(sol[0], sol[1])

    self.logger.info("whichXYTheta returned: {}".format(result))

    self.assertEqual(result, "theta", "Expected \"theta\" but received {}".format(result))

  def test_whichXYTheta_no_change_first_move(self):
    """Test helper function that finds if movement is to be in the XY plane or the theta dimension. This test checks steps with
    no previous move and no difference in any attribute."""

    sol = [{'cont_theta': '0.000',
    'cont_x': '3.350',
    'cont_y': '3.250',
    'theta': '0',
    'x': '33',
    'y': '32'},
    {'cont_theta': '0.000',
    'cont_x': '3.350',
    'cont_y': '3.250',
    'theta': '0',
    'x': '33',
    'y': '32'}]

    self.logger.debug("Testing whichXYTheta with sol: " + pp.pformat(sol))

    result = self.Nav.whichXYTheta(sol[0], sol[1])

    self.logger.info("whichXYTheta returned: {}".format(result))

    self.assertEqual(result, nav.errors["ERROR_NO_CHANGE"], "Expected {} but received \
      {}".format(nav.errors["ERROR_NO_CHANGE"], result))

  def test_whichXYTheta_x_change_xy_move(self):
    """Test helper function that finds if movement is to be in the XY plane or the theta dimension. This test checks steps with
    previous move in XY plane and difference in x value."""

    sol = [{'cont_theta': '0.000',
    'cont_x': '3.350',
    'cont_y': '3.250',
    'theta': '0',
    'x': None,
    'y': None},
    {'cont_theta': '0.000',
    'cont_x': '3.250',
    'cont_y': '3.250',
    'theta': '0',
    'x': '32',
    'y': '32'}]

    self.logger.debug("Testing whichXYTheta with sol: " + pp.pformat(sol))

    result = self.Nav.whichXYTheta(sol[0], sol[1])

    self.logger.info("whichXYTheta returned: {}".format(result))

    self.assertEqual(result, "xy", "Expected \"x\" but received {}".format(result))

  def test_whichXYTheta_y_change_xy_move(self):
    """Test helper function that finds if movement is to be in the XY plane or the theta dimension. This test checks steps with
    previous move in XY plane and difference in y value."""

    sol = [{'cont_theta': '0.000',
    'cont_x': '3.350',
    'cont_y': '3.250',
    'theta': '0',
    'x': None,
    'y': None},
    {'cont_theta': '0.000',
    'cont_x': '3.250',
    'cont_y': '3.250',
    'theta': '0',
    'x': '32',
    'y': '32'}]

    self.logger.debug("Testing whichXYTheta with sol: " + pp.pformat(sol))

    result = self.Nav.whichXYTheta(sol[0], sol[1])

    self.logger.info("whichXYTheta returned: {}".format(result))

    self.assertEqual(result, "xy", "Expected \"x\" but received {}".format(result))

  def test_whichXYTheta_theta_change_xy_move(self):
    """Test helper function that finds if movement is to be in the XY plane or the theta dimension. This test checks steps with
    previous move in XY plane and difference in y value."""

    sol = [{'cont_theta': '0.000',
    'cont_x': '3.350',
    'cont_y': '3.250',
    'theta': '1',
    'x': None,
    'y': None},
    {'cont_theta': '0.0625',
    'cont_x': '3.350',
    'cont_y': '3.250',
    'theta': '0',
    'x': '32',
    'y': '32'}]

    self.logger.debug("Testing whichXYTheta with sol: " + pp.pformat(sol))

    result = self.Nav.whichXYTheta(sol[0], sol[1])

    self.logger.info("whichXYTheta returned: {}".format(result))

    self.assertEqual(result, "theta", "Expected \"x\" but received {}".format(result))

  def test_whichXYTheta_x_change_theta_move(self):
    """Test helper function that finds if movement is to be in the XY plane or the theta dimension. This test checks steps with
    previous move in XY plane and difference in x value."""

    sol = [{'cont_theta': '0.000',
    'cont_x': '3.350',
    'cont_y': '3.250',
    'theta': None,
    'x': '33',
    'y': '32'},
    {'cont_theta': '0.000',
    'cont_x': '3.250',
    'cont_y': '3.250',
    'theta': '0',
    'x': '32',
    'y': '32'}]

    self.logger.debug("Testing whichXYTheta with sol: " + pp.pformat(sol))

    result = self.Nav.whichXYTheta(sol[0], sol[1])

    self.logger.info("whichXYTheta returned: {}".format(result))

    self.assertEqual(result, "xy", "Expected \"x\" but received {}".format(result))

  def test_whichXYTheta_y_change_theta_move(self):
    """Test helper function that finds if movement is to be in the XY plane or the theta dimension. This test checks steps with
    previous move in XY plane and difference in x value."""

    sol = [{'cont_theta': '0.000',
    'cont_x': '3.250',
    'cont_y': '3.350',
    'theta': None,
    'x': '32',
    'y': '33'},
    {'cont_theta': '0.000',
    'cont_x': '3.250',
    'cont_y': '3.250',
    'theta': '0',
    'x': '32',
    'y': '32'}]

    self.logger.debug("Testing whichXYTheta with sol: " + pp.pformat(sol))

    result = self.Nav.whichXYTheta(sol[0], sol[1])

    self.logger.info("whichXYTheta returned: {}".format(result))

    self.assertEqual(result, "xy", "Expected \"x\" but received {}".format(result))

  def test_whichXYTheta_theta_change_theta_move(self):
    """Test helper function that finds if movement is to be in the XY plane or the theta dimension. This test checks steps with
    previous move in XY plane and difference in x value."""

    sol = [{'cont_theta': '0.000',
    'cont_x': '3.250',
    'cont_y': '3.250',
    'theta': None,
    'x': '32',
    'y': '32'},
    {'cont_theta': '0.100',
    'cont_x': '3.250',
    'cont_y': '3.250',
    'theta': '2',
    'x': '32',
    'y': '32'}]

    self.logger.debug("Testing whichXYTheta with sol: " + pp.pformat(sol))

    result = self.Nav.whichXYTheta(sol[0], sol[1])

    self.logger.info("whichXYTheta returned: {}".format(result))

    self.assertEqual(result, "theta", "Expected \"x\" but received {}".format(result))

  def test_whichXYTheta_no_change_xy_move(self):
    """Test helper function that checks if the previous and current steps changed in the XY plane or the theta dimension, but not
    both. This test checks steps with no change in any attribute"""

    sol = [{'cont_theta': '0.000',
    'cont_x': '3.350',
    'cont_y': '3.250',
    'theta': '0',
    'x': None,
    'y': None},
    {'cont_theta': '0.000',
    'cont_x': '3.350',
    'cont_y': '3.250',
    'theta': '0',
    'x': '33',
    'y': '32'}]

    self.logger.debug("Testing whichXYTheta with sol: " + pp.pformat(sol))

    result = self.Nav.whichXYTheta(sol[0], sol[1])

    self.logger.info("whichXYTheta returned: {}".format(result))

    self.assertEqual(result, nav.errors["ERROR_NO_CHANGE"], "Expected {} but received \
      {}".format(nav.errors["ERROR_NO_CHANGE"], result))

  def test_whichXYTheta_no_change_theta_move(self):
    """Test helper function that checks if the previous and current steps changed in the XY plane or the theta dimension, but not
    both. This test checks steps with no change in any attribute"""

    sol = [{'cont_theta': '0.000',
    'cont_x': '3.350',
    'cont_y': '3.250',
    'theta': None,
    'x': '33',
    'y': '32'},
    {'cont_theta': '0.000',
    'cont_x': '3.350',
    'cont_y': '3.250',
    'theta': '0',
    'x': '33',
    'y': '32'}]

    self.logger.debug("Testing whichXYTheta with sol: " + pp.pformat(sol))

    result = self.Nav.whichXYTheta(sol[0], sol[1])

    self.logger.info("whichXYTheta returned: {}".format(result))

    self.assertEqual(result, nav.errors["ERROR_NO_CHANGE"], "Expected {} but received \
      {}".format(nav.errors["ERROR_NO_CHANGE"], result))


if __name__ == "__main__":
  unittest.main() # Execute all tests
