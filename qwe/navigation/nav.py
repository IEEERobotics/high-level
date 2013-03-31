#!/usr/bin/env python
"""Primary module of navigation package. 

As this develops, it will eventually accept a goalPose from planner, request a currentPose from localizer, then call
SBPL code (C++ made usable in Python by some method) and pass the configuration params. No file will be created and
no subprocess will spawn. The solution generated by SBPL will be returned to nav (not written to a file), and will then
be parsed and handed off to comm. Some additional logic involving issuing steps of the solution to comm, getting results,
checking for the amount of error, notifying localizer, maybe re-planning, and then issuing the next step will need to
be added."""

import logging.config
from collections import namedtuple
from subprocess import call
import os
from sys import exit
from math import sqrt, sin, cos, pi
from datetime import datetime
import pprint as pp

# Movement objects for issuing macro or micro movement commands to nav. Populate and pass to qMove_nav queue.
macro_move = namedtuple("macro_move", ["x", "y", "theta", "timestamp"])
micro_move_XY = namedtuple("micro_move_XY", ["distance", "speed", "timestamp"])
micro_move_theta = namedtuple("micro_move_theta", ["angle", "timestamp"])

# Dict of error codes and their human-readable names
errors = { 100 : "ERROR_BAD_CWD",  101 : "ERROR_SBPL_BUILD", 102 : "ERROR_SBPL_RUN", 103 : "ERROR_BUILD_ENV", 
  104 : "ERROR_BAD_RESOLUTION", 105 : "WARNING_SHORT_SOL", 106 : "ERROR_ARCS_DISALLOWED", 107 : "ERROR_DYNAMIC_DEM_UNKN", 108 :
  "ERROR_NO_CHANGE", 109 : "ERROR_FAILED_MOVE", 110 : "NO_SOL", 111 : "UNKNOWN_ERROR"}
errors.update(dict((v,k) for k,v in errors.iteritems())) # Converts errors to a two-way dict

# TODO These need to be calibrated
env_config = { "obsthresh" : "1", "cost_ins" : "1", "cost_cir" : "0", "cellsize" : "0.00635", "nominalvel" : "1.0", 
  "timetoturn45" : "2.0" }

config = { "steps_between_locs" : 5, "XYErr" : float(env_config["cellsize"]), "thetaErr" : .1}

class Nav:

  def __init__(self, bot_loc, course_map, waypoints, qNav_loc, scNav, bot_state, qMove_nav, logger):
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
    self.scNav = scNav
    self.bot_state = bot_state
    self.qMove_nav = qMove_nav
    self.logger = logger
    self.logger.debug("Passed-in data stored to Nav object")

  def start(self, doLoop=True):
    """Setup nav here. Finds path from cwd to qwe directory and then sets up paths from cwd to required files. Opens a file
    descriptor for /dev/null that can be used to suppress output. Compiles SBPL using a bash script. Unless doLoop param is True,
    calls the inf loop function to wait on motion commands to be placed in the qMove_nav queue.

    :param doLoop: Boolean value that when false prevents nav from entering the inf loop that processes movement commands. This
    can be helpful for testing."""
    self.logger.info("Started nav")

    # Find path to ./qwe directory. Allows for flexibility in the location nav is run from.
    # TODO Could make this arbitrary by counting the number of slashes
    if os.getcwd().endswith("qwe"):
      path_to_qwe = "./"
    elif os.getcwd().endswith("qwe/navigation"):
      path_to_qwe = "../"
    elif os.getcwd().endswith("qwe/navigation/tests"):
      path_to_qwe = "../../"
    else:
      self.logger.critical("Unexpected CWD: " + str(os.getcwd()))
      return errors["ERROR_BAD_CWD"]

    # Setup paths to required files
    self.build_env_script = path_to_qwe + "../scripts/build_env_file.sh"
    self.build_sbpl_script = path_to_qwe + "navigation/build_sbpl.sh"
    self.sbpl_executable = path_to_qwe + "navigation/sbpl/cmake_build/bin/test_sbpl"
    self.env_file = path_to_qwe + "navigation/envs/env.cfg"
    self.mprim_file = path_to_qwe + "navigation/mprim/prim_tip_priority_4inch_step3"
    self.map_file = path_to_qwe + "navigation/maps/binary_map.txt"
    self.sol_file = path_to_qwe + "navigation/sols/sol.txt"
    self.sol_dir = path_to_qwe + "navigation/sols"
    self.sbpl_build_dir = path_to_qwe + "navigation/sbpl/cmake_build"

    # Open /dev/null for suppressing SBPL output
    self.devnull = open("/dev/null", "w")
    self.logger.info("Opened file descriptor for writing to /dev/null")

    # Compile SBPL
    build_rv = call([self.build_sbpl_script, self.sbpl_build_dir])
    if build_rv != 0:
      self.logger.critical("Failed to build SBPL. Script return value was: " + str(build_rv))
      return errors["ERROR_SBPL_BUILD"]

    if doLoop: # Call main loop that will handle movement commands passed in via qMove_nav
      self.logger.debug("Calling main loop function")
      self.loop()
    else: # Don't call loop, return to caller 
      self.logger.info("Not calling loop. Individual functions should be called by the owner of this class object.")

  def genSol(self, goal_x, goal_y, goal_theta, env_config=env_config):
    """Use SBPL to generate a series of steps, within some set of acceptable motion primitives, that move the robot from the
    current location to the goal pose

    Eventually the SBPL code will be modified such that it can be called directly from here and params can be passed in-memory, to
    avoid file IP and spawning new processes.

    :param goal_x: X coordinate of goal pose
    :param goal_y: Y coordinate of goal pose
    :param goal_theta: Angle of goal pose
    :param env_config: Values used by SBPL in env.cfg file"""

    self.logger.debug("Generating plan")

    # Translate bot_loc into internal units
    curX = self.XYFrombot_locUC(self.bot_loc["x"])
    curY = self.XYFrombot_locUC(self.bot_loc["y"])
    curTheta = self.thetaFrombot_locUC(self.bot_loc["theta"])

    # Build environment file for input into SBPL
    # TODO Upgrade this to call SBPL directly, as described above
    # "Usage: ./build_env_file.sh <obsthresh> <cost_inscribed_thresh> <cost_possibly_circumscribed_thresh> <cellsize> <nominalvel>
    # <timetoturn45degsinplace> <start_x> <start_y> <start_theta> <end_x> <end_y> <end_theta> [<env_file> <map_file>]"
    self.logger.debug("env_config: " + "{obsthresh} {cost_ins} {cost_cir} {cellsize} {nominalvel} {timetoturn45}".format(**env_config))
    self.logger.debug("Current pose: {} {} {}".format(curX, curY, curTheta))
    self.logger.debug("Goal pose: {} {} {}".format(goal_x, goal_y, goal_theta))
    self.logger.debug("Map file: " + str(self.map_file))
    self.logger.debug("Environment file to write: " + str(self.env_file))

    build_env_rv = call([self.build_env_script, env_config["obsthresh"],
                                                env_config["cost_ins"],
                                                env_config["cost_cir"],
                                                env_config["cellsize"],
                                                env_config["nominalvel"],
                                                env_config["timetoturn45"],
                                                str(curX),
                                                str(curY),
                                                str(curTheta),
                                                str(goal_x),
                                                str(goal_y),
                                                str(goal_theta),
                                                str(self.env_file),
                                                str(self.map_file)])

    # Check results of build_env_script call
    if build_env_rv != 0:
      self.logger.critical("Failed to build env file. Script return value was: " + str(build_env_rv))
      return errors["ERROR_BUILD_ENV"]
    self.logger.info("Successfully built env file. Return value was: " + str(build_env_rv))

    # Run SBPL
    origCWD = os.getcwd()
    os.chdir(self.sol_dir)
    sbpl_rv = call([self.sbpl_executable, self.env_file, self.mprim_file])
    os.chdir(origCWD)

    # Check results of SBPL run
    if sbpl_rv == -6:
      self.logger.critical("Failed to run SBPL. SBPL return value was: " + str(sbpl_rv))
      return errors["ERROR_BAD_RESOLUTION"]
    if sbpl_rv < 0:
      self.logger.critical("Failed to run SBPL. SBPL return value was: " + str(sbpl_rv))
      return errors["ERROR_SBPL_RUN"]
    if sbpl_rv == 1:
      # No solution found
      self.logger.warning("SBPL failed to find a solution")
      return errors["NO_SOL"]
    self.logger.info("Successfully ran SBPL. Return value was: " + str(sbpl_rv))

    # Read solution file into memory and return it
    sol = []
    sol_lables = ["x", "y", "theta", "cont_x", "cont_y", "cont_theta"]
    for line in open(self.sol_file, "r").readlines():
      self.logger.debug("Read sol step: " + str(line).rstrip("\n"))
      sol.append(dict(zip(sol_lables, line.split())))
    self.logger.debug("Built sol list of dicts: " + pp.pformat(sol))

    # Convert all values to floats
    for step in sol:
      for key in step:
        step[key] = float(step[key])

    return sol
      
  def loop(self):
    """Main loop of nav. Blocks and waits for motion commands passed in on qMove_nav"""

    self.logger.debug("Entering inf motion command handling loop")
    while True:

      self.logger.info("Blocking while waiting for command from queue with ID: " + pp.pformat(self.qMove_nav))
      # Signal that we nav is no longer running and is waiting for a goal pose
      self.bot_state["naving"] = False
      move_cmd = self.qMove_nav.get()
      self.bot_state["naving"] = True
      self.logger.info("Received move command: " + pp.pformat(move_cmd))

      if type(move_cmd) == macro_move:
        self.logger.info("Move command is if type macro")
        rv = self.macroMove(x=self.XYFromMoveQUC(move_cmd.x), y=self.XYFromMoveQUC(move_cmd.y), \
          theta=self.thetaFromMoveQUC(move_cmd.theta))
      elif type(move_cmd) == micro_move_XY:
        self.logger.info("Move command is if type micro_move_XY")
        rv = self.microMoveXY(distance=self.XYFromMoveQUC(move_cmd.distance), speed=self.speedFromMoveQUC(move_cmd.speed))
      elif type(move_cmd) == micro_move_theta:
        self.logger.info("Move command is if type micro_move_theta")
        rv = self.microMoveTheta(angle=self.thetaFromMoveQUC(move_cmd.angle))
      elif type(move_cmd) == str and move_cmd == "die":
        self.logger.warning("Recieved die command, nav is exiting.")
        self.bot_state["naving"] = False
        exit(0)
      else:
        self.logger.warn("Move command is of unknown type")

      if rv is True:
        self.logger.info("Move command was sucessful")
      elif rv in errors:
        self.logger.info("Move command failed with error {}".format(errors[rv]))
      else:
        self.logger.info("Move command returned unknown value {}".format(rv))

  def macroMove(self, x, y, theta):
    """Handle global movement commands. Accept a goal pose and use SBPL + other logic to navigate to that goal pose.

    :param x: X coordinate of goal pose
    :param y: Y coordinate of goal pose
    :param theta: Angle of goal pose"""
    self.logger.info("Handling macro move to {} {} {}".format(x, y, theta))

    while True:

      # Translate bot_loc data into internal units
      curX = self.XYFrombot_locUC(self.bot_loc["x"])
      curY = self.XYFrombot_locUC(self.bot_loc["y"])
      curTheta = self.thetaFrombot_locUC(self.bot_loc["theta"])

      # Check if 'bot is at or close to the goal pose
      if self.locsEqual(x, y, theta, curX, curY, curTheta):
        self.logger.info("Macro move succeeded")
        return True

      # Generate solution
      self.logger.debug("macroMove requesting sol from ({}, {}, {}) to ({}, {}, {})".format(curX, curY, curTheta, x, y, theta))
      sol = self.genSol(x, y, theta)

      # Handle value returned by genSol
      if type(sol) is list:
        self.logger.info("macroMove received a solution list from genSol")
        comm_sol_result = self.communicateSol(sol)

        if comm_sol_result is errors["ERROR_FAILED_MOVE"]:
          self.logger.warning("Attempted move wasn't within error margins, re-computing solution and trying again")
          continue
        elif comm_sol_result is errors["WARNING_SHORT_SOL"]:
          self.logger.warn("Short solutions typically mean that we are very close to goal: " + errors[comm_sol_result])
          return comm_sol_result
        elif comm_sol_result in errors:
          self.logger.error("Error while communicating sol to low-level code: " + errors[comm_sol_result])
          return comm_sol_result
      else:
        self.logger.info("macroMove did not receive a valid solution from genSol")

        # If no solution could be found
        if sol is errors["NO_SOL"]:
          self.logger.warn("No solution could be found, exiting macroMove")
          # TODO Notify planner or anyone who wants to know
          return sol
        elif sol in errors: # Some other type of error (likely more serious)
          self.logger.error("genSol returned " + errors[sol])
          return sol
        else:
          self.logger.error("Non-list, unknown-error returned to macroMove by genSol: " + str(sol))
          return errors["UNKNOWN_ERROR"]

  def communicateSol(self, sol):
    """Accept a solution list to pass to low-level code. Will pass commands to comm, wait for a response, and check if the
    response is within some error tolerance. If it isn't, a new goal will be generated. If it is, the next step will be passed to
    comm. Localizer will be updated at every return from comm.

    :param sol: List of dicts that contains a set of steps, using acceptable mprims, from the current pose to the goal pose
    """
    self.logger.debug("Communicating a solution to comm")

    if len(sol) <= 1:
      self.logger.warning("Solution only has " + str(len(sol)) + " step(s) - likely within tolerance, not running again.")
      return errors["WARNING_SHORT_SOL"]

    cur_step = 0

    # Iterate over solution. Outer loop controls how many blind moves we do between localization runs.
    for i in range(1, len(sol), config["steps_between_locs"]):

      for j in range(i, min(i + config["steps_between_locs"], len(sol))):

        cur_step = cur_step + 1

        self.logger.info("Handling solution step {} of {}".format(cur_step, len(sol)))

        # Find the dynamic dimension between the current step and the previous step
        dyn_dem = self.whichXYTheta(sol[j-1], sol[j])

        if dyn_dem in errors:
          self.logger.error("whichXYTheta failed with " + errors[dyn_dem])
          return dyn_dem

        if dyn_dem == "xy":
          self.logger.info("Movement will be in XY plane")

          # Calculate goal distance change in XY plane
          distance_m = sqrt((sol[j]["cont_x"] - sol[j-1]["cont_x"])**2 + (sol[j]["cont_y"] - sol[j-1]["cont_y"])**2)
          self.logger.info("Next step of solution is to move {} meters in the XY plane".format(distance_m))

          # Pass distance to comm and block for response
          commResult_m = self.distFromCommUC(self.scNav.botMove(self.distToCommUC(distance_m)))
          self.logger.info("Comm returned XY movement feedback of {}".format(commResult_m))

          # Report move result to localizer ASAP
          self.feedLocalizerXY(commResult_m)

        elif dyn_dem == "theta":
          self.logger.info("Movement will be in theta dimension")

          # Calculate goal change in theta
          angle_rads = sol[j]["cont_theta"] - sol[j-1]["cont_theta"]
          self.logger.info("Next step of solution is to rotate {} radians in the theta dimension".format(angle_rads))

          # Pass distance to comm and block for response
          commResult_rads = self.angleFromCommUC(self.scNav.botTurnRel(self.angleToCommUC(angle_rads)))
          self.logger.info("Comm returned theta movement feedback of {}".format(commResult_rads))

          # Report move result to localizer ASAP
          self.feedLocalizerTheta(commResult_rads)

        else:
          self.logger.error("Unknown whichXYTheta result: " + str(dyn_dem))
          return errors["ERROR_DYNAMIC_DEM_UNKN"]

      # Localize TODO How? Assume move was perfect for now
      self.bot_loc["x"] = self.XYTobot_locUC(sol[cur_step]["cont_x"])
      self.bot_loc["y"] = self.XYTobot_locUC(sol[cur_step]["cont_y"])
      self.bot_loc["theta"] = self.thetaTobot_locUC(sol[cur_step]["cont_theta"])

      # Translate bot_loc into internal units
      curX = self.XYFrombot_locUC(self.bot_loc["x"])
      curY = self.XYFrombot_locUC(self.bot_loc["y"])
      curTheta = self.thetaFrombot_locUC(self.bot_loc["theta"])

      # Check if bot_loc is within some error of sol[i] and return errors["ERROR_FAILED_MOVE"] if it isn't TODO Units
      if self.locsEqual(sol[cur_step]["cont_x"], sol[cur_step]["cont_y"], sol[cur_step]["cont_theta"], curX, curY, curTheta):
        self.logger.info("Location is nearly what the solution dictates")
        continue
      else:
        self.logger.warn("Location is off from what solution dictates, need new solution")
        return errors["ERROR_FAILED_MOVE"]

  def distToCommUC(self, dist):
    """Convert from internal distance units (meters) to units used by comm for distances

    :param dist: Distance to convert from meters to comm distance units (mm)"""
    return float(dist) * 100

  def angleToCommUC(self, angle):
    """Convert from internal angle units (radians) to units used by comm for angles (tenths of degrees)

    :param angle: Angle to convert from radians to comm angle units"""
    return float(angle) * 57.2957795 * 10

  def distFromCommUC(self, commResult):
    """Convert result returned by comm for distance moves to internal units (meters)

    :param commResult: Distance result returned by comm (mm) to convert to meters"""
    return float(commResult) / 100

  def angleFromCommUC(self, commResult):
    """Convert result returned by comm for angle moves to internal units (radians)

    :param commResult: Angle result returned by comm to convert to radians"""
    return float(commResult) / 10 / 57.2957795

  def distToLocUC(self, dist):
    """Convert from internal distance units (meters) to units used by localizer for distances

    :param dist: Distance to convert from meters to localizer distance units (inches)"""
    return float(dist) / 0.0254

  def angleToLocUC(self, angle):
    """Convert from internal angle units (radians) to units used by localizer for angles

    :param dist: Angle to convert from radians to localizer angle units (radians)"""
    return float(angle)

  def XYFromMoveQUC(self, XY):
    """Convert XY value given by planner via qMove_nav to internal units (meters)

    :param XY: X or Y value (inches) given by planner via qMove_nav to convert to meters"""
    return 0.0254 * float(XY)

  def thetaFromMoveQUC(self, theta):
    """Convert theta value given by planner via qMove_nav to internal units (radians)

    :param XY: theta value given by planner via qMove_nav (radians) to convert to radians"""
    return float(theta)

  def speedFromMoveQUC(self, speed):
    """Convert speed value given by planner via qMove_nav to internal units

    :param speed: speed value given by planner via qMove_nav (in/sec) to convert to internal units (m/sec)"""
    return 0.0254 * float(speed)

  def XYFrombot_locUC(self, XY):
    """Convert XY value in bot_loc shared data to internal units (meters)

    :param XY: X or Y value used by bot_loc (inches) to convert to internal units (meters)"""
    return 0.0254 * float(XY)

  def thetaFrombot_locUC(self, theta):
    """Convert theta value in bot_loc shared data to internal units (radians)

    :param theta: theta value used by bot_loc (radians) to convert to internal units (radians)"""
    return float(theta)
  
  def XYTobot_locUC(self, XY):
    """Convert XY value in internal units (meters) to bot_loc shared data units (inches)

    :param XY: X or Y internal value (meters) to convert to units used by bot_loc (inches)"""
    return float(XY) / 0.0254  

  def thetaTobot_locUC(self, theta):
    """Convert theta value in internal units (radians) to bot_loc shared data units (radians)

    :param theta: theta internal value (radians) to convert to bot_loc units (radians)"""
    return float(theta)

  def feedLocalizerXY(self, commResult_m):
    """Give localizer information about XP plane move results. Also, package up sensor information and a timestamp.

    :param commResult_m: Move result reported by comm in meters"""

    sensor_data = self.scNav.getAllSensorData()
    self.qNav_loc.put({"commResult" : self.distToLocUC(commResult_m), "sensorData" : sensor_data, "timestamp" : datetime.now()})

  def feedLocalizerTheta(self, commResult_rads):
    """Give localizer information about theta dimension rotate results. Also, package up sensor information and a timestamp.

    :param commResult_rads: Turn result reported by comm in radians"""

    sensor_data = self.scNav.getAllSensorData()
    self.qNav_loc.put({"commResult" : self.angleToLocUC(commResult_rads), "sensorData" : sensor_data, "timestamp" : datetime.now()})

  def whichXYTheta(self, step_prev, step_cur):
    """Find if movement is to be in the XY plane or the theta dimension.

    :param step_prev: The older of the two steps. This was the move executed during the last cycle (or the start position)
    :param step_cur: Current solution step being executed"""

    if (step_prev["cont_theta"] != step_cur["cont_theta"] and step_prev["x"] != step_cur["x"] \
                                                          and step_prev["y"] != step_cur["y"]) \
                       or (step_prev["cont_theta"] != step_cur["cont_theta"] and step_prev["x"] != step_cur["x"]) \
                       or (step_prev["cont_theta"] != step_cur["cont_theta"] and step_prev["y"] != step_cur["y"]):
      self.logger.error("The previous and current steps involve a change in X, Y and theta - which is disallowed")
      return errors["ERROR_ARCS_DISALLOWED"]
    elif step_prev["cont_theta"] != step_cur["cont_theta"]:
      self.logger.debug("The previous step and current step involve a change in theta")
      return "theta"
    elif step_prev["x"] != step_cur["x"] or step_prev["y"] != step_cur["y"]:
      self.logger.debug("The previous step and the current step involve a change in XY")
      return "xy"
    else:
      self.logger.error("The previous and current steps have the same continuous values")
      return errors["ERROR_NO_CHANGE"]

  def locsEqual(self, x0, y0, theta0, x1, y1, theta1, acceptXYErr=config["XYErr"], acceptThetaErr=config["thetaErr"]):
    """Contains logic for checking if two poses are within some acceptable tolerance of each other.

    :param x0: Frst X coordinate to compare
    :param y0: Frst Y coordinate to compare
    :param theta0: Frst theta angle to compare
    :param x0: Second X coordinate to compare
    :param y0: Second Y coordinate to compare
    :param theta0: Second theta angle to compare
    :param acceptXYErr: Error in XY plane that is accepted
    :param acceptThetaErr: Error in theta dimension that is accepted"""

    self.logger.debug("Checking if {} {} {} equals {} {} {}".format(x0, y0, theta0, x1, y1, theta1))
    self.logger.debug("Acceptable error is {} for XY and {} for theta".format(acceptXYErr, acceptThetaErr))

    if (x0 - acceptXYErr) <= x1 and (x0 + acceptXYErr) >= x1 \
                                  and (y0 - acceptXYErr) <= y1 \
                                  and (y0 + acceptXYErr) >= y1 \
                                  and (theta0 - acceptThetaErr) <= theta1 \
                                  and (theta0 + acceptThetaErr) >= theta1:
      # Accept if locations are within given error
      self.logger.info("Locations are equal to within given error")
      return True
    else:
      # Rejct if locations are not within given error
      self.logger.info("Locations are not equal to within the given error")
      return False

  def microMoveXY(self, distance, speed):
    """Handle simple movements on a small scale. Used for small adjustments by vision or planner when very close to objects.

    :param distance: Distance to move in XY plane
    :param speed: Speed to execute move"""

    self.logger.debug("Handling micro move XY with distance {} and speed {}".format(distance, speed))

    # Pass distance to comm and block for response
    commResult_m = self.distFromCommUC(self.scNav.botMove(self.distToCommUC(distance, speed)))
    self.logger.info("Comm returned XY movement feedback of {}".format(commResult_m))

    # Report move result to localizer ASAP
    self.feedLocalizerXY(commResult_m)

    return True

  def microMoveTheta(self, angle):
    """Handle simple movements on a small scale. Used for small adjustments by vision or planner when very close to objects.

    :param angle: Theta change desired by micro move"""

    self.logger.debug("Handling micro move theta with angle {}".format(angle))

    # Pass distance to comm and block for response
    commResult_rads = self.angleFromCommUC(self.scNav.botMove(self.angleToCommUC(angle)))
    self.logger.info("Comm returned theta movement feedback of {}".format(commResult_rads))

    # Report move result to localizer ASAP
    self.feedLocalizerTheta(commResult_rads)

    return True

def run(bot_loc, course_map, waypoints, qNav_loc, scNav, bot_state, qMove_nav, logger=None):
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
  if logger is None:
    logging.config.fileConfig("logging.conf") # TODO This will break if not called from qwe. Add check to fix based on cwd?
    logger = logging.getLogger(__name__)
    logger.debug("Logger is set up")

  # Build nav object and start it
  logger.debug("Executing run function of nav")
  nav = Nav(bot_loc, course_map, waypoints, qNav_loc, scNav, bot_state, qMove_nav, logger)
  logger.debug("Built Nav object")
  return nav.start()
