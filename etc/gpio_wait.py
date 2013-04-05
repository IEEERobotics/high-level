#!/usr/bin/env python

"""Waits till GPIO pin 113 gets an interrupt (switch S1 is pressed) and returns."""
import commands

GPIO_WAIT_CMD="./gpio.o 113"

def runCommand(command):
  print ">", command
  status, output = commands.getstatusoutput(command)
  print output
  print "Return status:", status

def gpio_wait():
  runCommand(GPIO_WAIT_CMD)

if __name__ == "__main__":
  print "Waiting for GPIO button press..."
  gpio_wait()
  print "Button pressed! Done."
