#!/usr/bin/env python

"""Waits till GPIO pin 113 gets an interrupt (switch S1 is pressed) and returns."""
import commands

def runCommand(command):
  print ">", command
  status, output = commands.getstatusoutput(command)
  print output
  print "Return status:", status

def gpio_wait():
  runCommand("~/gpio.o 113")

if __name__ == "__main__":
  print "Waiting for GPIO button press..."
  gpio_wait()
  print "Button pressed! Done."
