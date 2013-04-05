#!/usr/bin/env python
"""Run a set of simple motion commands to qualify."""

import signal
from time import sleep
import comm.serial_interface as comm

def qualifier(sc, option=1, distance=4000, angle=450, speed=300): 
  # Units:- angle: 10ths of degree, distance: encoder counts (1000 ~= 6 in.), speed: PID value (200-1000)
  
  if option == 1:
    # Option 1: Turn while moving (arc)
    print "qualifier(): Command: botSet({distance}, {angle}, {speed})".format(distance=distance, angle=angle, speed=speed)
    actual_distance, actual_heading = sc.botSet(distance, angle, speed)
    print "qualifier(): Response: distance = {distance}, heading = {heading}".format(distance=actual_distance, heading=actual_heading)
  elif option == 2:
    # Option 2: Turn (abs. angle), then move
    print "qualifier(): Command : botTurnAbs({0})".format(angle)
    actual_heading = sc.botTurnAbs(angle)
    print "qualifier(): Response: heading = {0}".format(actual_heading)
    
    print "qualifier(): Command : botMove({0})".format(distance)
    actual_distance = sc.botMove(distance)
    print "qualifier(): Response: distance = {0}".format(actual_distance)
  else:
    print "qualifier(): Unknown option: {0}".format(option)


def main():
  # Serial interface and command
  print "main(): Creating SerialInterface process..."
  si = comm.SerialInterface(timeout=1.0)
  si.start()
  sc = comm.SerialCommand(si.commands, si.responses)
  
  # Set signal handlers
  live = True
  def handleSignal(signum, frame):
    if signum == signal.SIGTERM or signum == signal.SIGINT:
      print "main.handleSignal(): Termination signal ({0}); stopping comm loop...".format(signum)
    else:
      print "main.handleSignal(): Unknown signal ({0}); stopping comm loop anyways...".format(signum)
    #si.quit()
    live = False
  
  signal.signal(signal.SIGTERM, handleSignal)
  signal.signal(signal.SIGINT, handleSignal)
  
  # Zero compass heading
  sc.compassReset()
  
  # Qualifying moves
  sleep(2)  # delay to let button presser move back hand
  qualifier(sc)
  
  # Reset signal handlers to default behavior
  signal.signal(signal.SIGTERM, signal.SIG_DFL)
  signal.signal(signal.SIGINT, signal.SIG_DFL)
  
  sc.quit()
  si.join()
  print "main(): Done."


if __name__ == "__main__":
  main()