#!/usr/bin/env python
"""Primary module of navigation package. 

This code accepts a macro goal pose or a micro move command from planner. It then finds a path from the current location to the
goal pose using SBPL. The resulting path is comprised of valid moves given the motion primitives provided. The solution generated
by SBPL is used to issue rotate and move commands to the serial interface in comm, which pushes them down to the low-level code.
Responses returned by comm are used fed to localizer, who updates the bot's location. Once the location has been updated, nav
checks if the new current position is within an error tolerance of where its solution dictates. If it isn't, it generates a new
plan and repeats this process until the goal pose is reached. If the updated bot location is within nav's error tolerance, it
continues with the current plan."""

import logging.config
from collections import namedtuple
from subprocess import call
from os import chdir, getcwd
from sys import exit
from math import sqrt, degrees, radians
from datetime import datetime
import pprint as pp
from time import sleep
import numpy as np

# Movement objects for issuing macro or micro movement commands to nav. Populate and pass to qMove_nav queue.
macro_move = namedtuple("macro_move", ["x", "y", "theta", "timestamp"])
micro_move_XY = namedtuple("micro_move_XY", ["distance", "speed", "timestamp"])
micro_move_theta = namedtuple("micro_move_theta", ["angle", "timestamp"])
micro_move_XYTheta = namedtuple("micro_move_XYTheta", ["distance", "speed", "angle", "timestamp"])

# Dict of error codes and their human-readable names
errors = { 100 : "ERROR_BAD_CWD",  101 : "ERROR_SBPL_BUILD", 102 : "ERROR_SBPL_RUN", 103 : "ERROR_BUILD_ENV", 
  104 : "ERROR_BAD_RESOLUTION", 105 : "WARNING_SHORT_SOL", 106 : "ERROR_ARCS_DISALLOWED", 107 : "ERROR_DYNAMIC_DEM_UNKN", 108 :
  "ERROR_NO_CHANGE", 109 : "ERROR_FAILED_MOVE", 110 : "NO_SOL", 111 : "UNKNOWN_ERROR", 112 : "ERROR_SENSORS" }
errors.update(dict((v,k) for k,v in errors.iteritems())) # Converts errors to a two-way dict

# TODO These need to be calibrated
env_config = { "obsthresh" : "1", "cost_ins" : "1", "cost_cir" : "0", "cellsize" : "0.00635", "nominalvel" : "1000.0", 
  "timetoturn45" : "2", "max_sensor_tries" : 10 }

config = { "steps_between_locs" : 5, "XYErr" : (float(env_config["cellsize"]) * 50), "thetaErr" : (0.39269908169 * 1.5),
"loc_wait" : .01, "default_left_US" : 100, "default_right_US" : 100, "default_front_US" : 100, "default_back_US" : 100, 
"default_accel_x" : 0, "default_accel_y" : 0, "default_accel_z" : 980, "default_heading" : 0, "XY_mv_len" : .15 }

class Nav:

  def __init__(self, bot_loc, qNav_loc, scNav, bot_state, qMove_nav, logger, testQueue=None):
    """Setup navigation class

    :param bot_loc: Shared dict updated with best-guess location of bot by localizer
    :param qNav_loc: Multiprocessing.Queue object for passing movement feedback to localizer from navigator
    :param si: Serial interface object for sending commands to low-level boards
    :param bot_state: Dict of information about the current state of the bot (ex macro/micro nav)
    :param qMove_nav: Multiprocessing.Queue object for passing movement commands to navigation (mostly from Planner)
    :param logger: Used for standard Python logging
    :param testQueue: Used as a back channel for a fake localizer to update bot_loc with the ideal new pose
    """

    logger.info("Nav instantiated")

    # Store passed-in data
    self.bot_loc = bot_loc
    self.qNav_loc = qNav_loc
    self.scNav = scNav
    self.bot_state = bot_state
    self.qMove_nav = qMove_nav
    self.logger = logger
    self.testQueue = testQueue
    self.logger.debug("Passed-in data stored to Nav object")

  def start(self, doLoop=True):
    """Setup nav here. Finds path from cwd to qwe directory and then sets up paths from cwd to required files. Opens a file
    descriptor for /dev/null that can be used to suppress output. Compiles SBPL using a bash script. Unless doLoop param is True,
    calls the inf loop function to wait on motion commands to be placed in the qMove_nav queue.

    :param doLoop: Boolean value that when false prevents nav from entering the inf loop that processes movement commands. This
    can be helpful for testing."""
    self.logger.info("Started nav")

    self.logger.debug("CWD of nav is {}".format(getcwd()))

    # Find path to ./qwe directory. Allows for flexibility in the location nav is run from.
    # TODO Could make this arbitrary by counting the number of slashes
    if getcwd().endswith("qwe"):
      path_to_qwe = "./"
    elif getcwd().endswith("qwe/navigation"):
      path_to_qwe = "../"
    elif getcwd().endswith("qwe/navigation/tests"):
      path_to_qwe = "../../"
    else:
      self.logger.critical("Unexpected CWD: " + str(getcwd()))
      return errors["ERROR_BAD_CWD"]

    # Setup paths to required files
    self.build_env_script = path_to_qwe + "../scripts/build_env_file.sh"
    self.build_sbpl_script = path_to_qwe + "navigation/build_sbpl.sh"
    self.sbpl_executable = path_to_qwe + "navigation/sbpl/cmake_build/bin/test_sbpl"
    self.sbpl_exec_from_sol_dir = "../sbpl/cmake_build/bin/test_sbpl"
    self.env_file = path_to_qwe + "navigation/envs/env.cfg"
    self.env_file_from_sol_dir = "../envs/env.cfg"
    self.mprim_file = path_to_qwe + "navigation/mprim/prim_tip_priority_4inch_step3"
    self.mprim_file_from_sol_dir = "../mprim/prim_tip_priority_4inch_step3"
    self.map_file = path_to_qwe + "navigation/maps/binary_map.txt"
    self.sol_file = path_to_qwe + "navigation/sols/sol.txt"
    self.sol_dir = path_to_qwe + "navigation/sols"
    self.sbpl_build_dir = path_to_qwe + "navigation/sbpl/cmake_build"
    self.script_dir = path_to_qwe + "../scripts"

    # Open /dev/null for suppressing SBPL output
    #self.devnull = open("/dev/null", "w")
    #self.logger.info("Opened file descriptor for writing to /dev/null")

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
    self.logger.debug("env_config: {}".format(pp.pformat(env_config)))
    self.logger.debug("Current pose: {} {} {}".format(curX, curY, curTheta))
    self.logger.debug("Goal pose: {} {} {}".format(goal_x, goal_y, goal_theta))
    self.logger.debug("Map file: " + str(self.map_file))
    self.logger.debug("Environment file to write: " + str(self.env_file))
    self.logger.debug("Environment script to use {}".format(self.build_env_script))
    self.logger.debug("CWD: {}".format(getcwd()))

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
                                                str(self.map_file)],
                                                cwd=str(getcwd()))

    # Check results of build_env_script call
    if build_env_rv != 0:
      self.logger.critical("Failed to build env file. Script return value was: " + str(build_env_rv))
      return errors["ERROR_BUILD_ENV"]
    self.logger.info("Successfully built env file. Return value was: " + str(build_env_rv))

    # Run SBPL
    origCWD = getcwd()
    self.logger.debug("Changing dir from {}".format(origCWD))
    chdir(self.sol_dir)
    self.logger.debug("Running SBPL CWD {}".format(getcwd()))
    self.logger.debug("Running SBPL with executable {}".format(self.sbpl_exec_from_sol_dir))
    self.logger.debug("Running SBPL with env_file {}".format(self.env_file_from_sol_dir))
    self.logger.debug("Running SBPL with mprim_file {}".format(self.mprim_file_from_sol_dir))
    sbpl_rv = call([self.sbpl_exec_from_sol_dir, self.env_file_from_sol_dir, self.mprim_file_from_sol_dir])
    chdir(origCWD)

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
    #self.logger.debug("Built sol list of dicts: " + pp.pformat(sol))

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
      move_cmd = self.qMove_nav.get()
      #self.bot_state["naving"] = True
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
      elif type(move_cmd) == micro_move_XYTheta:
        self.logger.info("Move command is if type micro_move_XYTheta")
        rv = self.microMoveXYTheta(distance=self.XYFromMoveQUC(move_cmd.distance), speed=self.speedFromMoveQUC(move_cmd.speed), \
                                  angle=self.thetaFromMoveQUC(move_cmd.angle))
      elif type(move_cmd) == str and move_cmd == "die":
        self.logger.warning("Received die command, nav is exiting.")
        self.bot_state["naving"] = False

        if self.testQueue is not None:
          self.testQueue.put("die")

        self.bot_state["naving"] = False
        exit(0)
      else:
        self.logger.warn("Move command is of unknown type")

      if rv is True:
        self.logger.info("Move command was successful")
      elif rv in errors:
        self.logger.info("Move command failed with error {}".format(errors[rv]))
      else:
        self.logger.info("Move command returned unknown value {}".format(rv))

      self.bot_state["naving"] = False

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

        #self.logger.info("Sending solution to be cleaned up")
        #clean_sol = self.cleanSol(sol, curY, curX, curTheta)

        #comm_sol_result = self.communicateSol(clean_sol)
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
    for i in range(len(sol)):

      self.logger.info("Handling solution step {} of {}".format(i, len(sol)))

      # Find the dynamic dimension between the current step and the previous step
      if i != 0:
        dyn_dem = self.whichXYTheta(sol[i-1], sol[i])
      else:
        self.logger.debug("This is first move of sol, using bot_loc for prev step")
        dyn_dem = self.whichXYTheta({"cont_x" : self.XYFrombot_locUC(self.bot_loc["x"]), "cont_y" : \
                  self.XYFrombot_locUC(self.bot_loc["y"]), "cont_theta" : self.XYFrombot_locUC(self.bot_loc["theta"])}, sol[i])

      if dyn_dem == errors["ERROR_ARCS_DISALLOWED"] and i == 0:
        self.logger.debug("This is the first move of a solution and diff b/t bot_loc and first step is in XY and theta")

        # Calculate goal change in theta TODO Use bot_loc
        angle_rads = sol[i]["cont_theta"] - self.thetaFrombot_locUC(self.bot_loc["theta"])
        self.logger.info("Next step of solution is to rotate {} radians in the theta dimension".format(angle_rads))

        # Pass distance to comm and block for response
        commResult_rads = self.angleFromCommUC(self.scNav.botTurnRel(self.angleToCommUC(angle_rads)))
        self.logger.info("Comm returned theta movement feedback of {}".format(commResult_rads))

        # Report move result to localizer ASAP
        self.feedLocalizerTheta(commResult_rads)

      elif dyn_dem in errors and i != 0:
        self.logger.error("whichXYTheta failed with " + errors[dyn_dem])
        return dyn_dem

      elif dyn_dem == "xy":
        self.logger.info("Movement will be in XY plane")

        # Calculate goal distance change in XY plane
        distance_m = sqrt((sol[i]["cont_x"] - self.XYFrombot_locUC(self.bot_loc["x"]))**2 \
                        + (sol[i]["cont_y"] - self.XYFrombot_locUC(self.bot_loc["y"]))**2)
        self.logger.info("Next step of solution is to move {} meters in the XY plane".format(distance_m))

        # Pass distance to comm and block for response
        commResult_m = self.distFromCommUC(self.scNav.botMove(self.distToCommUC(distance_m)))
        self.logger.info("Comm returned XY movement feedback of {}".format(commResult_m))

        # Report move result to localizer ASAP
        self.feedLocalizerXY(commResult_m)

      elif dyn_dem == "theta":
        self.logger.info("Movement will be in theta dimension")

        # Calculate goal change in theta TODO Use bot_loc
        angle_rads = sol[i]["cont_theta"] - self.thetaFrombot_locUC(self.bot_loc["theta"])
        self.logger.info("Next step of solution is to rotate {} radians in the theta dimension".format(angle_rads))

        # Pass distance to comm and block for response
        commResult_rads = self.angleFromCommUC(self.scNav.botTurnRel(self.angleToCommUC(angle_rads)))
        self.logger.info("Comm returned theta movement feedback of {}".format(commResult_rads))

        # Report move result to localizer ASAP
        self.feedLocalizerTheta(commResult_rads)

      else:
        self.logger.error("Unknown whichXYTheta result: " + str(dyn_dem))
        return errors["ERROR_DYNAMIC_DEM_UNKN"]

      # If using a fake localizer, feed it the ideal location
      if self.testQueue is not None:
        self.logger.debug("Using testQueue")
        self.testQueue.put({ "x" : self.XYTobot_locUC(sol[i]["cont_x"]), "y" : self.XYTobot_locUC(sol[i]["cont_y"]), 
                            "theta" : self.thetaTobot_locUC(sol[i]["cont_theta"]) })

      # Wait for localizer to update bot_loc
      if self.bot_loc["dirty"]:
        self.logger.debug("Waiting for localizer to read commResult and set bot_loc[dirty] to False")
        while self.bot_loc["dirty"]:
          sleep(config["loc_wait"])

      # Translate bot_loc into internal units NOTE These will block until bot_loc is clean
      curX = self.XYFrombot_locUC(self.bot_loc["x"])
      curY = self.XYFrombot_locUC(self.bot_loc["y"])
      curTheta = self.thetaFrombot_locUC(self.bot_loc["theta"])

      # Check if bot_loc is within some error of sol[i] and return errors["ERROR_FAILED_MOVE"] if it isn't TODO Units
      if self.locsEqual(sol[i]["cont_x"], sol[i]["cont_y"], sol[i]["cont_theta"], curX, curY, curTheta):
        self.logger.info("Location is nearly what the solution dictates")
        continue
      else:
        self.logger.warn("Location is off from what solution dictates, need new solution")
        return errors["ERROR_FAILED_MOVE"]

  def cleanSol(self, sol, curX, curY, curTheta):
    """Convert solution generated by SBPL into one that that uses moves in the XY plane of a given size."""

    self.logger.debug("CleanSol was given sol: {}".format(pp.pformat(sol)))

    # Iterate over solution
    for i in range(len(sol)):

      # If this is not the first step of the solution
      if i != 0:
        # Find the dimension that changed between the previous step and this one
        dyn_dem = self.whichXYTheta(sol[i-1], sol[i])
      # If this was the first step of the solution
      else:
        # Find the dimension that changed between the current location (strat pose) and the first step of the solution
        dyn_dem = self.whichXYTheta({"cont_x" : self.XYFrombot_locUC(self.bot_loc["x"]), "cont_y" : \
                  self.XYFrombot_locUC(self.bot_loc["y"]), "cont_theta" : self.XYFrombot_locUC(self.bot_loc["theta"])}, sol[i])

      # Handle error
      if dyn_dem in errors:
        self.logger.error("whichXYTheta failed with " + errors[dyn_dem])
        return dyn_dem

      # If this step is part of an XY segment
      if dyn_dem == "xy":
        seg_theta = sol[i]["cont_theta"] 
        # If this is the first step of the XY segment
        if seg_disp == 0:
          
          # If this is not the first step of the solution
          if i != 0:
            # Store the first step of this XY segment
            start_seg = sol[i]
          # If this is the first step of the solution overall
          else:
            # Create a dict from the current location and store that as the first step of this XY segment
            start_seg = {"cont_x" : self.XYFrombot_locUC(self.bot_loc["x"]), "cont_y" : \
                  self.XYFrombot_locUC(self.bot_loc["y"]), "cont_theta" : self.XYFrombot_locUC(self.bot_loc["theta"])}

        # Calculate displacement
        distance_m = sqrt((sol[i]["cont_x"] - self.XYFrombot_locUC(self.bot_loc["x"]))**2 \
                        + (sol[i]["cont_y"] - self.XYFrombot_locUC(self.bot_loc["y"]))**2)

        seg_disp += distance_m

      # If this is the end of an XY segment or the end of the solution
      elif dyn_dem == "theta" or i == range(len(sol))[-1]:

        # Store the last step of this XY segment
        end_seg = sol[i-1]

        # Find the displacement of this XY segment
        seg_disp = sqrt((start_seg["x"] - end_seg["x"])**2 + (start_seg["y"] - end_seg["y"])**2)

        #for step_disp in np.arange(0, seg_disp, config["XY_mv_len"]):

        

        # If dyn_dem is XY
          # If seg_disp is 0, this is the start of an XY move segment
            # Store the XY of earlier val (either cur loc or sol[i-1]) as start_seg
            # Store theta of earlier val as seg_theta
          # Find disp and add it to seg disp

        # If dyn_dem is theta or we reach the end of the solution
          # Store xy of last XY step, which will be sol[i-1] as end_seg
          # Find disp in XY plane between start_seg and end_seg points and store as seg_disp

          # Iterate over seg_disp in increments of config["XY_mv_len"]
            # Use trig to find result XY of a move of len config["XY_mv_len"] from clean_sol[-1] along angle 
            # Add step to clean_sol with cont_x

    return sol

  def distToCommUC(self, dist):
    """Convert from internal distance units (meters) to units used by comm for distances. Also, since all move commands go through
    this function or angleToCommUC, set bot_loc to dirty here.

    :param dist: Distance to convert from meters to comm distance units (mm)"""

    #self.logger.debug("Translated XY move command from {} to {}".format(dist, float(dist) * 1000 ))
    encoder_units = float(dist) * 39.3701 * (1633/9.89)
    self.logger.debug("Translated XY move command from {} to {}".format(dist, encoder_units))

    # Mark location as dirty, since I'm about to issue a move command
    self.bot_loc["dirty"] = True
    self.logger.info("Bot loc is now marked as dirty")

    #return float(dist) * 1000 # This is in mm
    return int(round(encoder_units)) # This is in encoder units

  def speedToCommUC(self, speed):
    """Convert from internal distance units (meters) to units used by comm for distances. Also, since all move commands go through
    this function or angleToCommUC, set bot_loc to dirty here.

    :param dist: Distance to convert from meters to comm distance units (mm)"""

    #self.logger.debug("Translated XY move command from {} to {}".format(speed, float(speed) * 1000 ))
    encoder_units = float(speed) * 39.3701 * (1633/9.89)
    self.logger.debug("Translated XY move command from {} to {}".format(speed, encoder_units))

    # Mark location as dirty, since I'm about to issue a move command
    self.bot_loc["dirty"] = True
    self.logger.info("Bot loc is now marked as dirty")

    #return float(speed) * 1000 # This is in mm
    return int(round(encoder_units)) # This is in encoder units

  def angleToCommUC(self, angle):
    """Convert from internal angle units (radians) to units used by comm for angles (tenths of degrees). Also, since all move 
    commands go through this function or distToCommUC, set bot_loc to dirty here.


    :param angle: Angle to convert from radians to comm angle units"""

    degs = degrees(angle) % 360
    if degs > 180:
      degs = degs - 360
    tenths_degs = degs * 10
    #degs = degrees(angle)
    #tenths_degs = degs * 10

    self.logger.debug("Translated theta move command from {} to {}".format(angle, tenths_degs))

    # Mark location as dirty, since I'm about to issue a move command
    self.bot_loc["dirty"] = True
    self.logger.info("Bot loc is now marked as dirty")

    return int(round(tenths_degs))

  def distFromCommUC(self, commResult):
    """Convert result returned by comm for distance moves to internal units (meters)

    :param commResult: Distance result returned by comm (mm) to convert to meters"""

    # Assumes mm
    #self.logger.debug("translated xy commresult from {} to {}".format(commresult, float(commresult) / 1000))
    #return float(commResult) / 1000

    # Assumes encoder units
    commResult_m = commResult / (1633/9.89) / 39.3701
    self.logger.debug("translated xy commresult from {} to {}".format(commResult, commResult_m))
    return commResult_m

  def angleFromCommUC(self, commResult):
    """Convert result returned by comm for angle moves to internal units (radians)

    :param commResult: Angle result returned by comm to convert to radians"""

    degs = commResult / 10
    rads = radians(degs)
    #if degs < 0:
    #  degs = 360 + degs
    #rads = radians(degs)

    self.logger.debug("Translated theta commResult from {} to {}".format(commResult, rads))
    return rads

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

  def XYFrombot_locUC(self, XY, noBlock=False):
    """Convert XY value in bot_loc shared data to internal units (meters)

    :param XY: X or Y value used by bot_loc (inches) to convert to internal units (meters)"""

    self.logger.debug("XYFrombot_locUC translated {} to {}".format(XY, 0.0254 * float(XY)))
        
    return 0.0254 * float(XY)

  def thetaFrombot_locUC(self, theta, noBlock=False):
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

  def sensorsFromCommUC(self, sensor_data):
    """"Convert sensor data returned from comm into typical units. Heading is in tenths of degrees"""

    # US sensor result * .34 * 0.0393701 to get inches
    sensor_data["ultrasonic"]["left"] = float(sensor_data["ultrasonic"]["left"]) * 0.013385834
    sensor_data["ultrasonic"]["right"] = float(sensor_data["ultrasonic"]["right"]) * 0.013385834
    sensor_data["ultrasonic"]["front"] = float(sensor_data["ultrasonic"]["front"]) * 0.013385834
    sensor_data["ultrasonic"]["back"] = float(sensor_data["ultrasonic"]["back"]) * 0.013385834

    # Heading in tenths of degrees / 10 / 57.2957795 to get radians
    sensor_data["heading"] = float(sensor_data["heading"]) / 10 / 57.2957795

    # Acc unites in mm/sec**2 going to leave them that way for now

    return sensor_data

  def getSensorData(self):

    self.logger.debug("Polling sensors...")
    sensor_data = self.scNav.getAllSensorData()

    tries = 0

    while sensor_data["result"] is not True and tries < config["max_sensor_tries"]:
      self.logger.warning("Sensor data problem! {}".format(pp.pformat(sensor_data)))
      self.logger.info("Polling sensor again...")
      sensor_data = self.scNav.getAllSensorData()
      tries = tries + 1

    if sensor_data["result"] is not True:
      self.logger.error("Failed to get sensor data after {} attempts".format(config["max_sensor_tries"]))
      return errors["ERROR_SENSORS"]

    # Check if this was a real sensor data result, and if not build a fake one
    if "heading" not in sensor_data:
      self.logger.info("Sensor data was fake, building realistic fake one")
      sensor_data = { "result" : True, "msg" : "This is fake", "id" : 0, "heading" : config["default_heading"], 
                      "accel" : {"x" : config["default_accel_x"], "y" : config["default_accel_y"], 
                                 "z" : config["default_accel_z"]},
                      "ultrasonic" : {"left" : config["default_left_US"], "right" : config["default_right_US"], 
                                      "front" : config["default_front_US"], "back" : config["default_back_US"]}}
  
    self.logger.info("Sensor data from comm: {}".format(pp.pformat(sensor_data)))

    converted_sensor_data = self.sensorsFromCommUC(sensor_data)

    self.logger.info("Converted sensor data: {}".format(pp.pformat(converted_sensor_data)))
    return converted_sensor_data


  def feedLocalizerXY(self, commResult_m):
    """Give localizer information about XP plane move results. Also, package up sensor information and a timestamp.

    :param commResult_m: Move result reported by comm in meters"""


    sensor_data = self.getSensorData()
    self.logger.debug("About to put data into qNav_loc, object {}".format(str(self.qNav_loc)))
    self.qNav_loc.put({"dXY" : self.distToLocUC(commResult_m), "dTheta" : 0, "sensorData" : sensor_data, \
                                                                              "timestamp" : datetime.now()})
    self.logger.debug("Back from puting data into qNav_loc")

  def feedLocalizerTheta(self, commResult_rads):
    """Give localizer information about theta dimension rotate results. Also, package up sensor information and a timestamp.

    :param commResult_rads: Turn result reported by comm in radians"""

    sensor_data = self.getSensorData()
    self.logger.debug("About to put data into qNav_loc, object {}".format(str(self.qNav_loc)))
    self.qNav_loc.put({"dTheta" : self.angleToLocUC(commResult_rads), "dXY" : 0, "sensorData" : sensor_data, \
                                                                                  "timestamp" : datetime.now()})
    self.logger.debug("Back from puting data into qNav_loc")

  def feedLocalizerXYTheta(self, actual_dist, abs_heading):
    """Give localizer information about XY and theta results. Also, package up sensor information and a timestamp."""

    sensor_data = self.getSensorData()
    self.logger.debug("About to put data into qNav_loc, object {}".format(str(self.qNav_loc)))
    self.qNav_loc.put({"dTheta" : self.angleToLocUC(abs_heading), "dXY" : self.distToLocUC(actual_dist), \
                      "sensorData" : sensor_data, "timestamp" : datetime.now()})
    self.logger.debug("Back from puting data into qNav_loc")

  def whichXYTheta(self, step_prev, step_cur):
    """Find if movement is to be in the XY plane or the theta dimension.

    :param step_prev: The older of the two steps. This was the move executed during the last cycle (or the start position)
    :param step_cur: Current solution step being executed"""

    self.logger.debug("step_prev is {}, step_cur is {}".format(str(step_prev), str(step_cur)))
    prev_theta = round(float(step_prev["cont_theta"]), 5)
    prev_x = round(float(step_prev["cont_x"]), 5)
    prev_y = round(float(step_prev["cont_y"]), 5)

    cur_theta = round(float(step_cur["cont_theta"]), 5)
    cur_x = round(float(step_cur["cont_x"]), 5)
    cur_y = round(float(step_cur["cont_y"]), 5)

    self.logger.debug("Rounded, prev is ({} {} {}) and cur is ({} {} {})".format(prev_x, prev_y, prev_theta, cur_x, cur_y, \
                                                                                 cur_theta))

    if (prev_theta != cur_theta and prev_x != cur_x and prev_y != cur_y or prev_theta != cur_theta and prev_x != cur_x \
                                                                        or prev_theta != cur_theta and prev_y != cur_y):
      self.logger.error("The previous and current steps involve a change in X, Y and theta - which is disallowed")
      return errors["ERROR_ARCS_DISALLOWED"]
    elif prev_theta != cur_theta:
      self.logger.debug("The previous step and current step involve a change in theta")
      return "theta"
    elif prev_x != cur_x or prev_y != cur_y:
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

    # Mark location as dirty, since I'm about to issue a move command
    self.bot_loc["dirty"] = True
    self.logger.info("Bot loc is now marked as dirty")

    # Pass distance to comm and block for response
    commResult_m = self.distFromCommUC(self.scNav.botMove(self.distToCommUC(distance), speed))
    self.logger.info("Comm returned XY movement feedback of {}".format(commResult_m))

    # Report move result to localizer ASAP
    self.feedLocalizerXY(commResult_m)

    return True

  def microMoveTheta(self, angle):
    """Handle simple movements on a small scale. Used for small adjustments by vision or planner when very close to objects.

    :param angle: Theta change desired by micro move"""

    self.logger.debug("Handling micro move theta with angle {}".format(angle))

    # Mark location as dirty, since I'm about to issue a move command
    self.bot_loc["dirty"] = True
    self.logger.info("Bot loc is now marked as dirty")

    # Pass distance to comm and block for response
    commResult_rads = self.angleFromCommUC(self.scNav.botMove(self.angleToCommUC(angle)))
    self.logger.info("Comm returned theta movement feedback of {}".format(commResult_rads))

    # Report move result to localizer ASAP
    self.feedLocalizerTheta(commResult_rads)

    return True

  def microMoveXYTheta(self, distance, speed, angle):
    """Handle simple movements on a small scale. Used for small adjustments by vision or planner when very close to objects.

    :param angle: Theta change desired by micro move"""

    self.logger.debug("Handling micro move XYTheta with distance {}, speed {} and angle {}".format(distance, speed, angle))

    # Mark location as dirty, since I'm about to issue a move command
    self.bot_loc["dirty"] = True
    self.logger.info("Bot loc is now marked as dirty")

    # Pass distance to comm and block for response
    #commResult_rads = self.angleFromCommUC(self.scNav.botMove(self.angleToCommUC(angle)))
    actual_dist_comm_units, abs_heading_comm_units = self.scNav.botSet(self.distToCommUC(distance), self.speedToCommUC(speed), \
                                                                      self.angleToCommUC(angle))
    actual_dist = self.distFromCommUC(actual_dist_comm_units)
    abs_heading = self.angleFromCommUC(abs_heading_comm_units)

    self.logger.info("Comm returned actual_dist of {} and abs_heading of {}".format(actual_dist, abs_heading))

    # Report move result to localizer ASAP
    self.feedLocalizerXYTheta(actual_dist, abs_heading)

    return True

def run(bot_loc, qNav_loc, scNav, bot_state, qMove_nav, logger=None, testQueue=None):
  """Function that accepts initial data from controller and kicks off nav. Will eventually involve instantiating a class.

  :param bot_loc: Shared dict updated with best-guess location of bot by localizer
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
  nav = Nav(bot_loc, qNav_loc, scNav, bot_state, qMove_nav, logger, testQueue)
  logger.debug("Built Nav object")
  return nav.start()
