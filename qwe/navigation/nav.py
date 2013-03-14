#!/usr/bin/env python
"""Primary module of navigation package"""

import comm.serial_interface as comm

def run(bot_loc, blocks, zones, corners, course_map, waypoints):
  print "Nothing to see here"

def moveForward(distance, speed):
  """Very stupid function for moving forward. Goal is to get started with message passing between planner and comm."""
  si = comm.SerialInterface()
  actual_move = si.botMove(distance, speed)
  return actual_move
