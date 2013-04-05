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
from math import pi, radians, degrees, sqrt

# Dict of error codes and their human-readable names
errors = {100 : "ERROR_BAD_CWD"}
errors.update(dict((v,k) for k,v in errors.iteritems())) # Converts errors to a two-way dict

config = { "si_timeout" : .1 }

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
import localizer.localizer as localizer
import comm.serial_interface as comm

# Paths to various files from qwe
path_to_env = path_to_qwe + "navigation/envs/env.cfg"
path_to_sbpl = path_to_qwe + "navigation/sbpl/cmake_build/bin/test_sbpl"
path_to_sol = path_to_qwe + "navigation/sols/sol.txt"

def fakeLoc(testQueue, bot_loc, logger):
  while True:
    logger.info("testQueue is waiting on data")
    ideal_loc = testQueue.get()
    logger.info("testQueue received {}".format(pp.pformat(ideal_loc)))

    if type(ideal_loc) == str and ideal_loc == "die":
      logger.info("fakeLoc is exiting")
      sys.exit(0)

    bot_loc["x"] = ideal_loc["x"]
    bot_loc["y"] = ideal_loc["y"]
    bot_loc["theta"] = ideal_loc["theta"]

    logger.debug("fakeLoc set bot_loc to {} {} {}".format(bot_loc["x"], bot_loc["y"], bot_loc["theta"]))

    bot_loc["dirty"] = False
    logger.info("fakeLoc set bot_loc to clean")

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
    self.si = comm.SerialInterface(timeout=config["si_timeout"])
    self.si.start() # Displays an error if port not found (not running on Pandaboard)
    self.logger.info("Serial interface set up")

    # Build Queue objects for IPC. Name shows producer_consumer.
    self.qNav_loc = Queue()
    self.qMove_nav = Queue()
    self.logger.debug("Queue objects created")

    # Get map, waypoints
    self.course_map = mapper.unpickle_map(path_to_qwe + "mapping/map.pkl")
    self.logger.info("Map unpickled")
    self.waypoints = mapper.unpickle_waypoints(path_to_qwe + "mapping/waypoints.pkl")
    self.logger.info("Waypoints unpickled")

    # Build shared data structures
    self.manager = Manager()
    self.start_x = self.waypoints["start"][1][0]
    self.start_y = self.waypoints["start"][1][1]
    self.start_theta = self.waypoints["start"][2]
    self.logger.debug("Start waypoint is {}, {}, {}".format(self.start_x, self.start_y, self.start_theta))
    self.bot_loc = self.manager.dict(x=self.start_x, y=self.start_y, theta=self.start_theta, dirty=False)
    self.bot_state = self.manager.dict(nav_type=None, action_type=None)
    self.logger.debug("Shared data structures created")

    # Build nav object
    self.scNav = comm.SerialCommand(self.si.commands, self.si.responses)
    self.scNav.compassReset()
    self.Nav = nav.Nav(self.bot_loc, self.qNav_loc, self.scNav, self.bot_state, self.qMove_nav, \
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
    self.si = comm.SerialInterface(timeout=config["si_timeout"])
    self.si.start() # Displays an error if port not found (not running on Pandaboard)
    self.logger.info("Serial interface set up")

    # Build Queue objects for IPC. Name shows producer_consumer.
    self.qNav_loc = Queue()
    self.qMove_nav = Queue()
    self.testQueue = Queue()
    self.logger.debug("Queue objects created")

    # Get map, waypoints and map properties
    self.course_map = mapper.unpickle_map(path_to_qwe + "mapping/map.pkl")
    self.logger.info("Map unpickled")
    self.waypoints = mapper.unpickle_waypoints(path_to_qwe + "mapping/waypoints.pkl")
    self.logger.info("Waypoints unpickled")
    self.map_properties = mapper.unpickle_map_prop_vars(path_to_qwe + "mapping/map_prop_vars.pkl")
    self.logger.debug("Map properties unpickled")

    # Find start location
    self.start_x = self.waypoints["start"][1][0]
    self.start_y = self.waypoints["start"][1][1]
    self.start_theta = self.waypoints["start"][2]
    self.logger.debug("Start waypoint is {}, {}, {}".format(self.start_x, self.start_y, self.start_theta))

    # Build shared data structures
    self.manager = Manager()
    self.bot_loc = self.manager.dict(x=self.start_x, y=self.start_y, theta=self.start_theta, dirty=False)
    self.bot_state = self.manager.dict(nav_type=None, action_type=None, naving=False) #nav_type is "micro" or "macro"
    self.zones = self.manager.dict()
    self.logger.debug("Shared data structures created")
    self.bot_state["zone_change"] = 1

    # Start fakeLoc process
    #self.pfakeLoc = Process(target=fakeLoc, args=(self.testQueue, self.bot_loc, self.logger))
    #self.pfakeLoc.start()
    #self.logger.info("fakeLoc process started")

    # Start nav process
    self.scNav = comm.SerialCommand(self.si.commands, self.si.responses)
    self.scNav.compassReset()
    self.logger.debug("First possible sensor read: {}".format(str(self.scNav.getAllSensorData())))
    self.pNav = Process(target=nav.run, args=(self.bot_loc, self.qNav_loc, self.scNav, \
      self.bot_state, self.qMove_nav, self.logger))
    self.logger.debug("First possible sensor read: {}".format(str(self.scNav.getAllSensorData())))
    #self.pNav = Process(target=nav.run, args=(self.bot_loc, self.qNav_loc, self.scNav, \
    #  self.bot_state, self.qMove_nav, self.logger, self.testQueue))
    self.pNav.start()
    self.logger.info("Navigator process started")

    # Start localizer process, pass it shared data, waypoints, map_properties course_map and queue for talking to nav
    self.pLocalizer = Process(target=localizer.run, args=(self.bot_loc, self.zones, self.map_properties, self.course_map, \
      self.waypoints, self.qNav_loc, self.bot_state, self.logger))
    self.pLocalizer.start()
    self.logger.info("Localizer process started")

  def tearDown(self):
    """Close serial interface threads"""

    # Pass a die command to nav
    self.logger.info("Telling nav to die")
    self.qMove_nav.put("die")

    # Join nav process
    self.pNav.join() 
    self.logger.info("Joined navigation process")

    # Pass a die command to loc
    self.logger.info("Telling loc to die")
    self.qNav_loc.put("die")

    self.pLocalizer.join()
    self.logger.info("Joined localizer process")

    # Pass a die command to loc
    #self.pfakeLoc.join()
    #self.logger.info("Joined fakeLoc process")

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
    self.logger.debug("Building goal pose")

    # Build goal pose
    goal_x = float(self.bot_loc["x"])
    goal_y = float(self.bot_loc["y"])
    goal_theta = float(self.bot_loc["theta"])

    goal_pose = nav.macro_move(goal_x, goal_y, goal_theta, datetime.now())
    self.logger.debug("Created goal pose {}".format(pp.pformat(goal_pose)))

    # Send goal pose via queue
    self.logger.debug("About to send goal pose to queue with ID {}".format(str(self.qMove_nav)))
    self.qMove_nav.put(goal_pose)
    self.logger.debug("Put goal pose into queue")

  def test_start_nearly_at_goal(self):
    """Pass in a goal pose that's nearly the same as the start pose"""
    # Build goal pose that's the same as the start pose
    self.logger.debug("Building goal pose")

    # Build goal pose
    goal_x = float(self.bot_loc["x"]) + (float(nav.env_config["cellsize"]) / 2 / 0.0254)
    goal_y = float(self.bot_loc["y"]) + (float(nav.env_config["cellsize"]) / 2 / 0.0254)
    goal_theta = float(self.bot_loc["theta"]) + (nav.config["thetaErr"] / 2)

    goal_pose = nav.macro_move(goal_x, goal_y, goal_theta, datetime.now())
    self.logger.debug("Created goal pose {}".format(pp.pformat(goal_pose)))

    # Send goal pose via queue
    self.logger.debug("About to send goal pose to queue with ID {}".format(str(self.qMove_nav)))
    self.qMove_nav.put(goal_pose)
    self.logger.debug("Put goal pose into queue")

  @unittest.skip("Not very useful, and breaks when error changes")
  def test_simple_XY_move(self):
    """Pass in a goal pose that only differs on the XY plane from the start pose"""
    self.logger.debug("Building goal pose")

    # Build goal pose
    goal_x = float(self.bot_loc["x"]) + (float(nav.env_config["cellsize"]) * 20 / 0.0254)
    goal_y = float(self.bot_loc["y"]) + (float(nav.env_config["cellsize"]) * 25 / 0.0254)
    #goal_x = float(self.bot_loc["x"]) + (nav.config["XYerr"] * 20 / 0.0254)
    #goal_y = float(self.bot_loc["y"]) + (nav.config["XYErr"] * 25 / 0.0254)
    goal_theta = float(self.bot_loc["theta"])

    goal_pose = nav.macro_move(goal_x, goal_y, goal_theta, datetime.now())
    self.logger.debug("Created goal pose {}".format(pp.pformat(goal_pose)))

    # Send goal pose via queue
    self.logger.debug("About to send goal pose to queue with ID {}".format(str(self.qMove_nav)))
    self.qMove_nav.put(goal_pose)
    self.logger.debug("Put goal pose into queue")

  @unittest.skip("Not very useful, and breaks when error changes")
  def test_simple_theta_move(self):
    """Pass in a goal pose that's different from the goal pose in the theta dimension only"""
    self.logger.debug("Building goal pose")

    # Build goal pose
    goal_x = float(self.bot_loc["x"])
    goal_y = float(self.bot_loc["y"])
    goal_theta = float(self.bot_loc["theta"]) + (nav.config["thetaErr"] * 3)

    goal_pose = nav.macro_move(goal_x, goal_y, goal_theta, datetime.now())
    self.logger.debug("Created goal pose {}".format(pp.pformat(goal_pose)))

    # Send goal pose via queue
    self.logger.debug("About to send goal pose to queue with ID {}".format(str(self.qMove_nav)))
    self.qMove_nav.put(goal_pose)
    self.logger.debug("Put goal pose into queue")

  @unittest.skip("Not very useful, and breaks when error changes")
  def test_simple_XYTheta_move(self):
    """Pass in a goal pose that differes in X, Y and theta from the start pose"""
    self.logger.debug("Building goal pose")

    # Build goal pose
    goal_x = float(self.bot_loc["x"]) + (float(nav.env_config["cellsize"]) * 20 / 0.0254)
    goal_y = float(self.bot_loc["y"]) + (float(nav.env_config["cellsize"]) * 25 / 0.0254)
    goal_theta = float(self.bot_loc["theta"]) + (nav.config["thetaErr"] * 3)

    goal_pose = nav.macro_move(goal_x, goal_y, goal_theta, datetime.now())
    self.logger.debug("Created goal pose {}".format(pp.pformat(goal_pose)))

    # Send goal pose via queue
    self.logger.debug("About to send goal pose to queue with ID {}".format(str(self.qMove_nav)))
    self.qMove_nav.put(goal_pose)
    self.logger.debug("Put goal pose into queue")

  @unittest.skip("Not very useful, and breaks when error changes")
  def test_two_moves(self):
    """Pass two moves to nav before telling it to die"""
    self.logger.debug("Building goal pose")

    # Build goal pose
    goal_x0 = float(self.bot_loc["x"]) + (float(nav.env_config["cellsize"]) * 20 / 0.0254)
    goal_y0 = float(self.bot_loc["y"]) + (float(nav.env_config["cellsize"]) * 25 / 0.0254)
    goal_theta0 = float(self.bot_loc["theta"]) + (nav.config["thetaErr"] * 3)

    goal_pose0 = nav.macro_move(goal_x0, goal_y0, goal_theta0, datetime.now())
    self.logger.debug("Created goal pose {}".format(pp.pformat(goal_pose0)))

    # Send goal pose via queue
    self.logger.debug("About to send goal pose to queue with ID {}".format(str(self.qMove_nav)))
    self.qMove_nav.put(goal_pose0)
    self.logger.debug("Put goal pose into queue")

    # Build goal pose
    goal_x1 = float(self.bot_loc["x"]) - (float(nav.env_config["cellsize"]) * 10 / 0.0254)
    goal_y1 = float(self.bot_loc["y"]) - (float(nav.env_config["cellsize"]) * 10 / 0.0254)
    goal_theta1 = float(self.bot_loc["theta"]) + (nav.config["thetaErr"] * 6)

    goal_pose1 = nav.macro_move(goal_x1, goal_y1, goal_theta1, datetime.now())
    self.logger.debug("Created goal pose {}".format(pp.pformat(goal_pose1)))

    # Send goal pose via queue
    self.logger.debug("About to send goal pose to queue with ID {}".format(str(self.qMove_nav)))
    self.qMove_nav.put(goal_pose1)
    self.logger.debug("Put goal pose into queue")

  def test_move_to_loading(self):
    """Pass in a goal pose that differes in X, Y and theta from the start pose"""
    self.logger.debug("Building goal pose")

    # Build goal pose
    goal_x = self.waypoints["St01"][1][0]
    goal_y = self.waypoints["St01"][1][1]
    goal_theta = self.waypoints["St01"][2]

    goal_pose = nav.macro_move(goal_x, goal_y, goal_theta, datetime.now())
    self.logger.debug("Created goal pose {}".format(pp.pformat(goal_pose)))

    # Send goal pose via queue
    self.logger.debug("About to send goal pose to queue with ID {}".format(str(self.qMove_nav)))
    self.qMove_nav.put(goal_pose)
    self.logger.debug("Put goal pose into queue")

  def test_move_to_loading_then_land(self):
    """Pass in a goal pose that differes in X, Y and theta from the start pose"""
    self.logger.debug("Building goal pose")

    # Build goal pose
    goal_x0 = self.waypoints["St01"][1][0]
    goal_y0 = self.waypoints["St01"][1][1]
    goal_theta0 = self.waypoints["St01"][2]

    goal_pose0 = nav.macro_move(goal_x0, goal_y0, goal_theta0, datetime.now())
    self.logger.debug("Created goal pose {}".format(pp.pformat(goal_pose0)))

    # Send goal pose via queue
    self.logger.debug("About to send goal pose to queue with ID {}".format(str(self.qMove_nav)))
    self.qMove_nav.put(goal_pose0)
    self.logger.debug("Put goal pose into queue")

    goal_x1 = self.waypoints["L06"][1][0]
    goal_y1 = self.waypoints["L06"][1][1]
    goal_theta1 = self.waypoints["L06"][2]

    goal_pose1 = nav.macro_move(goal_x1, goal_y1, goal_theta1, datetime.now())
    self.logger.debug("Created goal pose {}".format(pp.pformat(goal_pose1)))

    # Send goal pose via queue
    self.logger.debug("About to send goal pose to queue with ID {}".format(str(self.qMove_nav)))
    self.qMove_nav.put(goal_pose1)
    self.logger.debug("Put goal pose into queue")

  def test_start_to_L01(self):
    """Pass in a goal pose that differes in X, Y and theta from the start pose"""
    self.logger.debug("Building goal pose")

    # Build goal pose
    goal_x = self.waypoints["L01"][1][0]
    goal_y = self.waypoints["L01"][1][1]
    goal_theta = self.waypoints["L01"][2]

    goal_pose = nav.macro_move(goal_x, goal_y, goal_theta, datetime.now())
    self.logger.debug("Created goal pose {}".format(pp.pformat(goal_pose)))

    # Send goal pose via queue
    self.logger.debug("About to send goal pose to queue with ID {}".format(str(self.qMove_nav)))
    self.qMove_nav.put(goal_pose)
    self.logger.debug("Put goal pose into queue")

  def test_turn_90(self):
    goal_x = self.waypoints["start"][0][0] * float(nav.env_config["cellsize"]) * 39.3701
    goal_y = self.waypoints["start"][0][1] * float(nav.env_config["cellsize"]) * 39.3701
    goal_theta = pi/2

    goal_pose = nav.macro_move(goal_x, goal_y, goal_theta, datetime.now())
    self.logger.debug("Created goal pose {}".format(pp.pformat(goal_pose)))

    # Send goal pose via queue
    self.logger.debug("About to send goal pose to queue with ID {}".format(str(self.qMove_nav)))
    self.qMove_nav.put(goal_pose)
    self.logger.debug("Put goal pose into queue")

class TestCleanSol(unittest.TestCase):

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
    self.si = comm.SerialInterface(timeout=config["si_timeout"])
    self.si.start() # Displays an error if port not found (not running on Pandaboard)
    self.logger.info("Serial interface set up")

    # Build Queue objects for IPC. Name shows producer_consumer.
    self.qNav_loc = Queue()
    self.qMove_nav = Queue()
    self.logger.debug("Queue objects created")

    # Get map, waypoints
    self.waypoints = mapper.unpickle_waypoints(path_to_qwe + "mapping/waypoints.pkl")
    self.logger.info("Waypoints unpickled")

    # Build shared data structures
    self.manager = Manager()
    self.start_x = self.waypoints["start"][1][0]
    self.start_y = self.waypoints["start"][1][1]
    self.start_theta = self.waypoints["start"][2]
    self.logger.debug("Start waypoint is {}, {}, {}".format(self.start_x, self.start_y, self.start_theta))
    self.bot_loc = self.manager.dict(x=self.start_x, y=self.start_y, theta=self.start_theta, dirty=False)
    self.bot_state = self.manager.dict(nav_type=None, action_type=None)
    self.logger.debug("Shared data structures created")

    # Build nav object
    self.scNav = comm.SerialCommand(self.si.commands, self.si.responses)
    self.scNav.compassReset()
    self.Nav = nav.Nav(self.bot_loc, self.qNav_loc, self.scNav, self.bot_state, self.qMove_nav, \
      self.logger)
    self.logger.info("Nav object instantiated")

    self.Nav.start(doLoop=False)
    self.logger.info("Started nav object")

  def tearDown(self):
    """Close serial interface threads"""

    self.logger.removeHandler(self.file_handler)
    self.logger.removeHandler(self.stream_handler)

    self.scNav.quit()
    self.si.join()

  @unittest.expectedFailure
  def test_start_to_L01(self):
    """Create a solution from start to L01 and clean its XY moves to be of a given size."""

    # Build goal pose
    goal_x = self.Nav.XYFromMoveQUC(self.waypoints["L01"][1][0])
    goal_y = self.Nav.XYFromMoveQUC(self.waypoints["L01"][1][1])
    goal_theta = self.Nav.thetaFromMoveQUC(self.waypoints["L01"][2])
    self.logger.info("Goal pose is {} {} {}".format(goal_x, goal_y, goal_theta))

    # Generate solution using SBPL

    #self.logger.debug("Need solution from {} {} {} to {} {} {}
    sol = self.Nav.genSol(goal_x, goal_y, goal_theta)
    self.logger.info("Built solution: {}".format(pp.pformat(sol)))

    # Convert XY translations to be of desired length
    clean_sol = self.Nav.cleanSol(sol)
    self.logger.info("Cleaned solution: {}".format(pp.pformat(clean_sol)))

    # Setup some initial vars
    total_dx, total_dy, total_dTheta, total_disp, disp, last_disp, last_dyn_dem = 0, 0, 0, 0, 0, None, None

    for i in range(1, len(clean_sol)):
      # Find which dimension changed between these steps
      dyn_dem = self.Nav.whichXYTheta(clean_sol[i-1], clean_sol[i])
      self.logger.debug("Dynamic dimension was {}".format(dyn_dem))

      # Confirm that change was in XY or theta, not both
      self.assertNotEqual(dyn_dem, nav.errors["ERROR_ARCS_DISALLOWED"], "Arc encountered!")

      if dyn_dem == "xy":
        # Find dx and dy between last step and this step
        dx = clean_sol[i]["cont_x"] - clean_sol[i-1]["cont_x"]
        dy = clean_sol[i]["cont_y"] - clean_sol[i-1]["cont_y"]
        self.logger.debug("(dx, dy) was ({}, {})".format(dx, dy))

        # Find XY plane displacement between last step and this step
        disp = sqrt(dx**2 + dy**2)
        self.logger.debug("XY displacement was {}".format(disp))

        # Confirm that the displacement was less than or equal to the user-defined ideal displacement
        self.assertLessEqual(disp, nav.config["XY_mv_len"], "Change XY ({}) is larger than expected ({})".format(disp, \
                                                              nav.config["XY_mv_len"]))

        # If this is a series of XY moves, check that the previous one was of correct len
        if last_dyn_dem == "xy":
          self.assertEqual(last_disp, nav.config["XY_mv_len"], "Non-last in XY move series ({}) wasn't full len ({})".format( \
                                                                last_disp, nav.config["XY_mv_len"]))

        # Update dx and dy sums
        total_dx += dx
        total_dy += dy
        total_disp += disp
        self.logger.debug("(total_dx, total_dy, total_disp) is ({}, {}, {})".format(total_dx, total_dy, total_disp))
      elif dyn_dem == "theta":
        # Calculate dTheta
        dTheta = clean_sol[i]["cont_theta"] - clean_sol[i-1]["cont_theta"]
        self.logger.debug("dTheta is {}".format(dTheta))

        # Update dTheta sum
        total_dTheta += dTheta
        self.logger.debug("total_dTheta is {}".format(total_dTheta))
      else:
        # This would indicate an error in whichXYTheta
        self.fail("Unknown dynamic dimension {}, check whichXYTheta".format(dyn_dem))

      # Update past-state vars for displacement and dynamic dimension
      last_disp = disp
      last_dyn_dem = dyn_dem

    exptd_total_disp = sqrt((sol[-1]["cont_x"] - sol[0]["cont_x"])**2 + (sol[-1]["cont_y"] - sol[0]["cont_y"])**2)
    exptd_total_dx = sol[-1]["cont_x"] - sol[0]["cont_x"]
    exptd_total_dy = sol[-1]["cont_y"] - sol[0]["cont_y"]

    self.logger.info("Expected totals (disp, dx, dy) are ({}, {}, {})".format(exptd_total_disp, exptd_total_dx, \
                                                                              exptd_total_dy))

    self.assertAlmostEqual(total_disp, exptd_total_disp, places=4, msg="Total disp {} not close enough to expected {}".format( \
                                                                      total_disp, exptd_total_disp))
    self.assertAlmostEqual(total_dx, exptd_total_dx, places=4, msg="Total dx {} not close enough to expected {}".format( \
                                                                      total_dx, exptd_total_dx))
    self.assertAlmostEqual(total_dy, exptd_total_dy, places=4, msg="Total dt {} not close enough to expected {}".format( \
                                                                      total_dy, exptd_total_dy))

    self.assertAlmostEqual(sol[0]["cont_x"], clean_sol[0]["cont_x"], "Start X of sol ({}) != clean sol ({})".format( \
                                                                      sol[0]["cont_x"], clean_sol[0]["cont_x"]))
    self.assertAlmostEqual(sol[0]["cont_y"], clean_sol[0]["cont_y"], "Start Y of sol ({}) != clean sol ({})".format( \
                                                                      sol[0]["cont_y"], clean_sol[0]["cont_y"]))
    self.assertAlmostEqual(sol[0]["cont_theta"], clean_sol[0]["cont_theta"], "Start theta of sol ({}) != clean sol({}) ".format( \
                                                                      sol[0]["cont_theta"], clean_sol[0]["cont_theta"]))
class TestUC(unittest.TestCase):

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
    self.si = comm.SerialInterface(timeout=config["si_timeout"])
    self.si.start() # Displays an error if port not found (not running on Pandaboard)
    self.logger.info("Serial interface set up")

    # Build Queue objects for IPC. Name shows producer_consumer.
    self.qNav_loc = Queue()
    self.qMove_nav = Queue()
    self.logger.debug("Queue objects created")

    # Get map, waypoints
    self.waypoints = mapper.unpickle_waypoints(path_to_qwe + "mapping/waypoints.pkl")
    self.logger.info("Waypoints unpickled")

    # Build shared data structures
    self.manager = Manager()
    self.start_x = self.waypoints["start"][1][0]
    self.start_y = self.waypoints["start"][1][1]
    self.start_theta = self.waypoints["start"][2]
    self.logger.debug("Start waypoint is {}, {}, {}".format(self.start_x, self.start_y, self.start_theta))
    self.bot_loc = self.manager.dict(x=self.start_x, y=self.start_y, theta=self.start_theta, dirty=False)
    self.bot_state = self.manager.dict(nav_type=None, action_type=None)
    self.logger.debug("Shared data structures created")

    # Build nav object
    self.scNav = comm.SerialCommand(self.si.commands, self.si.responses)
    self.scNav.compassReset()
    self.Nav = nav.Nav(self.bot_loc, self.qNav_loc, self.scNav, self.bot_state, self.qMove_nav, \
      self.logger)
    self.logger.info("Nav object instantiated")

  def tearDown(self):
    """Close serial interface threads"""

    self.logger.removeHandler(self.file_handler)
    self.logger.removeHandler(self.stream_handler)

    self.scNav.quit()
    self.si.join()

  def test_debug0(self):
    """Testing translation from comm units to radians for debuging"""

    commResult = -113.48034456
    actual_result = 6.08512474229
    desired_result = -0.1980605648869636

    result0 = self.Nav.angleFromCommUC(commResult)
    self.assertEqual(result0, desired_result, "Failed to convert {} signed tenths of degrees to {} rads, result was {}".format( \
                                                                                  commResult, desired_result, actual_result))

  def test_XY_bot_loc_UC(self):

    testVal_in = 7.125
    testVal_m = 0.180975

    valNavUnits = self.Nav.XYFrombot_locUC(testVal_in)

    self.assertEqual(valNavUnits, testVal_m)

    valExUnits = self.Nav.XYTobot_locUC(valNavUnits)

    self.assertEqual(valExUnits, testVal_in)

  def test_distToCommUC(self):
    """Test converting meters to encoder units"""

    testVal_m0 = .5
    testVal_enc0 = int(round(testVal_m0 * 39.3701 * (1633/9.89)))

    result0 = self.Nav.distToCommUC(testVal_m0)
    self.assertEqual(testVal_enc0, result0, "Failed to convert {} meters to {} ECs, result was {} ECs".format( \
                                                                            testVal_m0, testVal_enc0, result0))

    testVal_m1 = 10
    testVal_enc1 = int(round(testVal_m1 * 39.3701 * (1633/9.89)))

    result1 = self.Nav.distToCommUC(testVal_m1)
    self.assertEqual(testVal_enc1, result1, "Failed to convert {} meters to {} ECs, result was {} ECs".format( \
                                                                            testVal_m1, testVal_enc1, result1))

    testVal_m2 = .001
    testVal_enc2 = int(round(testVal_m2 * 39.3701 * (1633/9.89)))

    result2 = self.Nav.distToCommUC(testVal_m2)
    self.assertEqual(testVal_enc2, result2, "Failed to convert {} meters to {} ECs, result was {} ECs".format( \
                                                                            testVal_m2, testVal_enc2, result2))

  def test_distFromCommUC(self):
    """Test converting encoder units to meters"""

    testVal_m0 = .5
    testVal_enc0 = testVal_m0 * 39.3701 * (1633/9.89)

    result0 = self.Nav.distFromCommUC(testVal_enc0)
    self.assertEqual(testVal_m0, result0, "Failed to convert {} ECs to {} meters, result was {} meters".format( \
                                                                            testVal_enc0, testVal_m0, result0))

    testVal_m1 = 10
    testVal_enc1 = testVal_m1 * 39.3701 * (1633/9.89)

    result1 = self.Nav.distFromCommUC(testVal_enc1)
    self.assertEqual(testVal_m1, result1, "Failed to convert {} ECs to {} meters, result was {} meters".format( \
                                                                            testVal_enc1, testVal_m1, result1))

    testVal_m2 = .001
    testVal_enc2 = testVal_m2 * 39.3701 * (1633/9.89)

    result2 = self.Nav.distFromCommUC(testVal_enc2)
    self.assertEqual(testVal_m2, result2, "Failed to convert {} ECs to {} meters, result was {} meters".format( \
                                                                            testVal_enc2, testVal_m2, result2))

  def test_angleToCommUC(self):

    testVal_rad0 = pi/2
    testVal_comm0 = 900

    result0 = self.Nav.angleToCommUC(testVal_rad0)
    self.assertEqual(testVal_comm0, result0, "Failed to convert {} rads to {} signed tenths of degs, result was {}".format( \
                                                                                       testVal_rad0, testVal_comm0, result0))

    testVal_rad0 = pi
    testVal_comm0 = 1800

    result0 = self.Nav.angleToCommUC(testVal_rad0)
    self.assertEqual(testVal_comm0, result0, "Failed to convert {} rads to {} signed tenths of degs, result was {}".format( \
                                                                                       testVal_rad0, testVal_comm0, result0))

    testVal_rad0 = 3*pi/2
    testVal_comm0 = -900

    result0 = self.Nav.angleToCommUC(testVal_rad0)
    self.assertEqual(testVal_comm0, result0, "Failed to convert {} rads to {} signed tenths of degs, result was {}".format( \
                                                                                       testVal_rad0, testVal_comm0, result0))

    testVal_rad0 = 2*pi
    testVal_comm0 = 0

    result0 = self.Nav.angleToCommUC(testVal_rad0)
    self.assertEqual(testVal_comm0, result0, "Failed to convert {} rads to {} signed tenths of degs, result was {}".format( \
                                                                                       testVal_rad0, testVal_comm0, result0))

    testVal_rad0 = 3*pi
    testVal_comm0 = 1800

    result0 = self.Nav.angleToCommUC(testVal_rad0)
    self.assertEqual(testVal_comm0, result0, "Failed to convert {} rads to {} signed tenths of degs, result was {}".format( \
                                                                                       testVal_rad0, testVal_comm0, result0))

    testVal_rad0 = 100*pi
    testVal_comm0 = 0

    result0 = self.Nav.angleToCommUC(testVal_rad0)
    self.assertEqual(testVal_comm0, result0, "Failed to convert {} rads to {} signed tenths of degs, result was {}".format( \
                                                                                       testVal_rad0, testVal_comm0, result0))

    testVal_rad0 = -pi/2
    testVal_comm0 = -900

    result0 = self.Nav.angleToCommUC(testVal_rad0)
    self.assertEqual(testVal_comm0, result0, "Failed to convert {} rads to {} signed tenths of degs, result was {}".format( \
                                                                                       testVal_rad0, testVal_comm0, result0))

    testVal_rad0 = -3*pi/2
    testVal_comm0 = 900

    result0 = self.Nav.angleToCommUC(testVal_rad0)
    self.assertEqual(testVal_comm0, result0, "Failed to convert {} rads to {} signed tenths of degs, result was {}".format( \
                                                                                       testVal_rad0, testVal_comm0, result0))

    testVal_rad0 = .001*pi
    testVal_comm0 = int(round(1.8000000000000002))

    result0 = self.Nav.angleToCommUC(testVal_rad0)
    self.assertEqual(testVal_comm0, result0, "Failed to convert {} rads to {} signed tenths of degs, result was {}".format( \
                                                                                       testVal_rad0, testVal_comm0, result0))


  def test_angleFromCommUC(self):

    testVal_rad0 = pi/2
    testVal_comm0 = 900

    result0 = self.Nav.angleFromCommUC(testVal_comm0)
    self.assertEqual(testVal_rad0, result0, "Failed to convert {} signed tenths of degrees to {} rads, result was {}".format( \
                                                                                       testVal_comm0, testVal_rad0, result0))

    testVal_rad0 = pi
    testVal_comm0 = 1800

    result0 = self.Nav.angleFromCommUC(testVal_comm0)
    self.assertEqual(testVal_rad0, result0, "Failed to convert {} signed tenths of degrees to {} rads, result was {}".format( \
                                                                                       testVal_comm0, testVal_rad0, result0))

    testVal_rad0 = round(-1.570796326793, 5)
    testVal_comm0 = -900

    result0 = round(self.Nav.angleFromCommUC(testVal_comm0), 5)
    self.assertEqual(testVal_rad0, result0, "Failed to convert {} signed tenths of deg to {} rads, rst was {}".format( \
                                                                                       testVal_comm0, testVal_rad0, result0))

    testVal_rad0 = 0
    testVal_comm0 = 0

    result0 = self.Nav.angleFromCommUC(testVal_comm0)
    self.assertEqual(testVal_rad0, result0, "Failed to convert {} signed tenths of degrees to {} rads, result was {}".format( \
                                                                                       testVal_comm0, testVal_rad0, result0))

    testVal_rad0 = pi
    testVal_comm0 = 1800

    result0 = self.Nav.angleFromCommUC(testVal_comm0)
    self.assertEqual(testVal_rad0, result0, "Failed to convert {} signed tenths of degrees to {} rads, result was {}".format( \
                                                                                       testVal_comm0, testVal_rad0, result0))

    testVal_rad0 = 0
    testVal_comm0 = 0

    result0 = self.Nav.angleFromCommUC(testVal_comm0)
    self.assertEqual(testVal_rad0, result0, "Failed to convert {} signed tenths of degrees to {} rads, result was {}".format( \
                                                                                       testVal_comm0, testVal_rad0, result0))


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
    self.si = comm.SerialInterface(timeout=config["si_timeout"])
    self.si.start() # Displays an error if port not found (not running on Pandaboard)
    self.logger.info("Serial interface set up")

    # Build Queue objects for IPC. Name shows producer_consumer.
    self.qNav_loc = Queue()
    self.qMove_nav = Queue()
    self.logger.debug("Queue objects created")

    # Get map, waypoints
    self.course_map = mapper.unpickle_map(path_to_qwe + "mapping/map.pkl")
    self.logger.info("Map unpickled")
    self.waypoints = mapper.unpickle_waypoints(path_to_qwe + "mapping/waypoints.pkl")
    self.logger.info("Waypoints unpickled")

    # Build shared data structures
    self.manager = Manager()
    self.start_x = self.waypoints["start"][1][0]
    self.start_y = self.waypoints["start"][1][1]
    self.start_theta = self.waypoints["start"][2]
    self.logger.debug("Start waypoint is {}, {}, {}".format(self.start_x, self.start_y, self.start_theta))
    self.bot_loc = self.manager.dict(x=self.start_x, y=self.start_y, theta=self.start_theta, dirty=False)
    self.bot_state = self.manager.dict(nav_type=None, action_type=None)
    self.logger.debug("Shared data structures created")

    # Build nav object
    self.scNav = comm.SerialCommand(self.si.commands, self.si.responses)
    self.scNav.compassReset()
    self.Nav = nav.Nav(self.bot_loc, self.qNav_loc, self.scNav, self.bot_state, self.qMove_nav, \
      self.logger)
    self.logger.info("Nav object instantiated")

  def tearDown(self):
    """Close serial interface threads"""

    self.logger.removeHandler(self.file_handler)
    self.logger.removeHandler(self.stream_handler)

    self.scNav.quit()
    self.si.join()

  def test_locsEqual_default_config_mixed_sign_twice_error(self):
    """Test function that's to check if two poses are equal to within some error. This test uses twice the acceptable error and
    mixed negative and positive values"""

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
    mixed negative and positive values"""

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
    negative values"""

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

    self.assertTrue(result, "locsEqual returned False with negative values and diff of half the acceptable error")

  def test_locsEqual_default_config_neg_vals_twice_error(self):
    """Test function that's to check if two poses are equal to within some error. This test uses twice the acceptable error and
    negative values"""

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

    self.assertFalse(result, "locsEqual returned True with negative values and with diff twice of acceptable error")

  def test_locsEqual_default_config_neg_vals_0_error(self):
    """Test function that's to check if two poses are equal to within some error. This test uses zero error and negative values."""

    self.logger.info("Testing locsEqual with {} {} {} and {} {} {}".format(-1, -.5, -.25, -1, -.5, -.25))

    result = self.Nav.locsEqual(-1, -.5, -.25, -1, -.5, -.25)

    self.logger.debug("locsEqual returned {}".format(result))

    self.assertTrue(result, "locsEqual returned False with negative values and zero error")

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
    self.si = comm.SerialInterface(timeout=config["si_timeout"])
    self.si.start() # Displays an error if port not found (not running on Pandaboard)
    self.logger.info("Serial interface set up")

    # Build shared data structures
    self.manager = Manager()
    self.bot_loc = self.manager.dict(x=1, y=1, theta=0, dirty=False) # Same params used in the env1.txt example file
    self.bot_state = self.manager.dict(nav_type=None, action_type=None)
    self.logger.debug("Shared data structures created")

    # Build Queue objects for IPC. Name shows producer_consumer.
    self.qNav_loc = Queue()
    self.qMove_nav = Queue()
    self.logger.debug("Queue objects created")

    # Get map, waypoints
    self.course_map = mapper.unpickle_map(path_to_qwe + "mapping/map.pkl")
    self.logger.info("Map unpickled")
    self.waypoints = mapper.unpickle_waypoints(path_to_qwe + "mapping/waypoints.pkl")
    self.logger.info("Waypoints unpickled")

    # Build nav object
    self.scNav = comm.SerialCommand(self.si.commands, self.si.responses)
    self.scNav.compassReset()
    self.Nav = nav.Nav(self.bot_loc, self.qNav_loc, self.scNav, self.bot_state, self.qMove_nav, \
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
