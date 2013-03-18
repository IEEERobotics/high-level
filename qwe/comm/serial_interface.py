"""
Primary communication module to interact with motor and sensor controller board over serial.
"""

import sys
import random
import serial
import threading
import Queue

default_port = "/dev/ttyO3"
default_baudrate = 19200
default_timeout = 1  # seconds; float allowed
default_queue_maxsize = 10

default_speed = 400
default_servo_ramp = 10

command_eol = "\r\n"

# TODO move arm info out into action, creating an Arm class to encapsulate?
left_arm = 0
right_arm = 2

arm_angles = { left_arm: (670, 340),
               right_arm: (340, 670) }  # arm: (up, down)

grippers = { left_arm: 1, right_arm: 3}
# TODO get correct gripper angles
gripper_angles = { grippers[left_arm]: (200, 400),
                   grippers[right_arm]: (200, 400) }  # gripper: (open, close)

class SerialInterface:
  """
  Encapsulates functionality to send (multiplexed) commands over a serial line.
  Exposes a set of methods for different navigation, action and sensor commands.
  """
  
  def __init__(self, port=default_port, baudrate=default_baudrate, timeout=default_timeout):
    self.port = port
    self.baudrate = baudrate
    self.timeout = timeout
    # NOTE Other default port settings: bytesize=8, parity='N', stopbits=1, xonxoff=0, rtscts=0
    self.device = None  # open serial port in start()
    
    # TODO move queue out to separate class to manage it (and responses?)
    self.commands = Queue.Queue(default_queue_maxsize)  # internal queue to receive and service commands
    # TODO create multiple queues for different priority levels?
    self.responses = { }  # a map structure to store responses by commandId
  
  def start(self):
    """Open serial port and start main loop thread/process."""
    try:
      self.device = serial.Serial(self.port, self.baudrate, timeout=self.timeout)  # open serial port
    except serial.serialutil.SerialException as e:
      print "SerialInterface.start(): Error: %s" % e
      return False
    
    if self.device.isOpen():
      print "SerialInterface.start(): Serial port \"%s\" open (Baud rate: %d, timeout: %d secs.)" % (self.device.name, self.device.baudrate, (-1 if self.timeout is None else self.timeout))
      self.device.flushInput()
      self.device.flushOutput()
    else:
      print "SerialInterface.start(): Unspecified error opening serial port \"%s\"" % self.port
      return False
    
    self.loopThread = threading.Thread(target=self.loop)
    self.loopThread.start()
    # TODO use multiprocessing and multiprocessing.Queue instead of threading and Queue
    
    return True
  
  def loop(self):
    """Main loop: Monitor queue for commands and service them until signaled to quit."""
    print "SerialInterface.loop(): Starting main [LOOP]..."
    while True:
      try:
        (commandId, command) = self.commands.get(True)  # blocks indefinitely
        if command == "quit":  # special "quit" command breaks out of loop
          break
        #print "[LOOP] Command : " + command
        
        response = self.execCommand(command)
        if response is None:  # None response means something went wrong, break out of loop
          break
        elif response.startswith("ERROR"):
          print "[LOOP] Error response: " + response
          #response = "ERROR"  # modify response since it is useless anyways?
        
        self.responses[commandId] = response  # store result by commandId for later retrieval
      except Queue.Empty:
        print "[LOOP] Empty queue"
        pass  # if queue is empty, simply loop back and wait for more commands
    
    # Clean up: Close serial port
    print "SerialInterface.loop(): Main loop terminated."
    if self.device is not None and self.device.isOpen():
      self.device.close()
      print "SerialInterface.loop(): Serial port closed"
    
    # Clean up: Clear queue and responses dict (print warning if there are unserviced commands?)
    if not self.commands.empty():
      print "SerialInterface.loop(): Warning: Terminated with pending commands"
    self.commands = None  # TODO find a better way to simply clear the queue (get items until empty?)
    self.responses.clear()
  
  def stop(self):
    """Stop main loop by sending quit command."""
    self.putCommand("quit")
  
  def execCommand(self, command):
    """Execute command (send over serial port) and return response. Adds terminating EOL chars. to commands and strips them from responses."""
    try:
      self.device.write(command + command_eol)  # add eol
      response = self.device.readline()
      return response.strip()  # strip EOL
    except Exception as e:
      print "SerialInterface.execCommand(): Error: " + e
      return None
  
  def putCommand(self, command):  # priority=0
    commandId = random.randrange(sys.maxint)  # generate unique command ID
    self.commands.put((commandId, command))  # insert command into queue as 2-tuple (ID, command)
    # TODO insert into appropriate queue by priority?
    return commandId  # return ID
  
  def getResponse(self, commandId, block=True):
    if block:
      while not commandId in self.responses:
        pass  # if blocking, wait till command has been serviced
    elif not commandId in self.responses:
      return None  # if non-blocking and command hasn't been serviced, return None
    
    response = self.responses.pop(commandId)  # get response and remove it
    return response
  
  def runCommandSync(self, command):
    """Convenience method for running a command and blocking for response."""
    commandId = self.putCommand(command)
    response = self.getResponse(commandId)
    return response
  
  def botStop(self):
    """Stop immediately."""
    response = self.runCommandSync("stop")
    return response.startswith("OK")
  
  def botSetSpeed(self, left, right):
    """Set individual wheel/side speeds (units: PWM values 0 - 10000)."""
    response = self.runCommandSync("pwm_drive {0} {1}".format(left, right))
    return response.startswith("OK")
  
  def botMove(self, distance, speed=default_speed):
    response = self.runCommandSync("set 0 {speed} {distance}".format(speed=speed, distance=distance))
    return 0  # TODO accept actual values once implemented in motor-control
    #return (0 if response.startswith("ERROR") else int(response))  # convert response (distance traveled) to int unless ERROR
  
  def botTurn(self, angle, speed=default_speed):
    response = self.runCommandSync("set {angle} {speed} 0".format(angle=(angle*10), speed=speed))  # angle is 10ths of degrees
    return 0  # TODO accept actual values once implemented in motor-control
    #return (0 if response.startswith("ERROR") else int(response))  # convert response (angle turned) to int (and divide by 10) unless ERROR
  
  def botSetHeading(self, angle, speed):
    pass  # TODO get current heading, compute difference, send turn command, wait for completion ack, return current heading (absolute)
  
  def armSetAngle(self, arm, angle, ramp=default_servo_ramp):
    response = self.runCommandSync("servo {channel} {ramp} {angle}".format(channel=arm, ramp=ramp, angle=angle))
    # TODO wait here for servo to reach angle?
    return response.startswith("OK")
  
  def armUp(self, arm):
    return self.armSetAngle(arm, arm_angles[arm][0])
  
  def armDown(self, arm):
    return self.armSetAngle(arm, arm_angles[arm][1])
  
  def gripperSetAngle(self, arm, angle, ramp=default_servo_ramp):
    response = self.runCommandSync("servo {channel} {ramp} {angle}".format(channel=grippers[arm], ramp=ramp, angle=angle))
    # TODO wait here for servo to reach angle?
    return response.startswith("OK")
  
  def gripperOpen(self, arm):
    gripper = grippers[arm]
    return gripperSetAngle(gripper, gripper_angles[gripper][0])
  
  def gripperClose(self, arm):
    gripper = grippers[arm]
    return gripperSetAngle(gripper, gripper_angles[gripper][1])
  
  def getAllSensorData(self):
    pass  # TODO obtain data for all sensors return them (timestamp?)
  
  def getSensorValue(self, sensorId):
    """Fetches current value of a sensor. Handles only scalar sensors, i.e. ones that return a single int value."""
    response = self.runCommandSync("sensor {sensorId}".format(sensorId=sensorId))
    # TODO timestamp sensor data here?
    return (-1 if response.startswith("ERROR") else int(response))  # NOTE this only handles single-value data
  
   # TODO write specialized sensor value fetchers for non-scalar sensors like the accelerometer (and possibly other sensors for convenience)


def main():
  """
  Standalone testing program for SerialInterface.
  Usage:
    python serial_interface.py [port [baudrate [timeout]]]
  """
  port = default_port
  baudrate = default_baudrate
  timeout = default_timeout
  
  if len(sys.argv) > 1:
    port = sys.argv[1]
    if len(sys.argv) > 2:
      baudrate = int(sys.argv[2])
      if len(sys.argv) > 3:
        timeout = None if sys.argv[3] == "None" else float(sys.argv[3])
  
  print "main(): Creating SerialInterface(port=\"{port}\", baudrate={baudrate}, timeout={timeout})".format(port=port, baudrate=baudrate, timeout=(-1 if timeout is None else timeout))
  serialInterface = SerialInterface(port, baudrate, timeout)
  if not serialInterface.start():
    return
  
  print "main(): Starting interactive session [Ctrl+D or \"quit\" to end]...\n"

  while True:
    try:
      command = raw_input("Me    : ")  # input command from user
    except EOFError:
      command = "quit"
    
    commandId = serialInterface.putCommand(command)
    if command == "quit":
      print "\nmain(): Exiting interactive session..."
      break
    
    response = serialInterface.getResponse(commandId)
    print "Device: " + response + " [" + str(commandId) + "]"
  
  #serialInterface.stop()
  print "main(): Done."


if __name__ == "__main__":
  main()
