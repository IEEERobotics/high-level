"""
Primary communication module to interact with motor and sensor controller board over serial.
"""

import sys
import json
import random
import serial
import threading
from multiprocessing import Process, Queue, Manager
from Queue import Empty as Queue_Empty
from time import sleep

import test

default_port = "/dev/ttyO3"
default_baudrate = 19200
default_timeout = 10  # seconds; float allowed
default_queue_maxsize = 10

default_speed = 400  # TODO set correct default speed when units are established
default_servo_ramp = 10  # 0-63; 10 is a good number

command_eol = "\r\n"
is_sequential = True  # force sequential execution of commands
prefix_id = False  # send id pre-pended with commands?
servo_delay = 1.0  # secs.; duration to sleep after sending a servo command to let it finish (motor-controller returns immediately)
fake_delay = 0.001  # secs.; duration to sleep for when faking serial comm.

# TODO move arm info out into action, creating an Arm class to encapsulate?
left_arm = 0
right_arm = 2

arm_angles = { left_arm: (670, 340),
               right_arm: (340, 670) }  # arm: (up, down)

grippers = { left_arm: 1, right_arm: 3 }
# TODO get correct gripper angles
gripper_angles = { grippers[left_arm]: (200, 400),
                   grippers[right_arm]: (200, 400) }  # gripper: (open, close)

sensors = { "heading": 0,  # compass / magnetometer
            "accel_x": 1,
            "accel_y": 2,
            "accel_z": 3,
            "ultrasonic_left": 4,
            "ultrasonic_front": 5,
            "ultrasonic_right": 6,
            "ultrasonic_back": 7 }

class SerialInterface(Process):
  """Encapsulates functionality to send (multiplexed) commands over a serial line."""
  
  def __init__(self, port=default_port, baudrate=default_baudrate, timeout=default_timeout, commands=None, responses=None):
    Process.__init__(self)
    
    self.port = port
    self.baudrate = baudrate
    self.timeout = timeout
    # NOTE Other default port settings: bytesize=8, parity='N', stopbits=1, xonxoff=0, rtscts=0
    self.device = None  # open serial port in run()
    self.live = False  # flag to signal threads
    
    # Create data structures to store commands and responses, unless passed in
    #self.sendLock = Lock()  # to prevent multiple processes from trying to send on the same serial line
    if commands is not None:
      self.commands = commands
    else:
      self.commands = Queue(default_queue_maxsize)  # internal queue to receive and service commands
    # TODO move queue out to separate class to manage it (and responses?)
    # TODO create multiple queues for different priority levels?
    
    if responses is not None:
      self.responses = responses
    else:
      self.manager = Manager()  # to facilitate process-safe shared memory, especially for responses; NOTE breaks on windows
      self.responses = self.manager.dict()  # a map structure to store responses by some command id
  
  def run(self):
    """Open serial port, and start send and receive threads."""
    # Open serial port
    try:
      self.device = serial.Serial(self.port, self.baudrate, timeout=self.timeout)  # open serial port
    except serial.serialutil.SerialException as e:
      print "SerialInterface.run(): Error: %s" % e
    
    # Flush input and output stream to clear any pending data; if port not available, fake it!
    if self.device is not None and self.device.isOpen():
      print "SerialInterface.run(): Serial port \"%s\" open (Baud rate: %d, timeout: %d secs.)" % (self.device.name, self.device.baudrate, (-1 if self.timeout is None else self.timeout))
      self.device.flushInput()
      self.device.flushOutput()
    else:
      print "SerialInterface.run(): Trouble opening serial port \"%s\"" % self.port
      print "SerialInterface.run(): Warning: Faking serial communications!"
      self.device = None  # don't quit, fake it
      self.send = self.fakeSend
      self.recv = self.fakeRecv
    
    if(is_sequential):
      # Start sequential execution (send + receive) thread
      print "SerialInterface.run(): Starting exec thread..."
      self.live = True
      
      self.execThread = threading.Thread(target=self.execLoop, name="EXEC")
      self.execThread.start()
      
      # Wait for thread to finish
      self.execThread.join()
      print "SerialInterface.run(): Exec thread joined."
    else:
      # Start send and receive threads
      print "SerialInterface.run(): Starting send and receive threads..."
      self.live = True
      
      self.sendThread = threading.Thread(target=self.sendLoop, name="SEND")
      self.sendThread.start()
      
      self.recvThread = threading.Thread(target=self.recvLoop, name="RECV")
      self.recvThread.start()
      
      # Wait for threads to finish
      self.sendThread.join()
      self.recvThread.join()
      print "SerialInterface.run(): Send and receive threads joined."
    
    # Clean up: Clear queue; print warning if there are unserviced commands
    if not self.commands.empty():
      print "SerialInterface.run(): Warning: Terminated with pending command(s)"
      # TODO clear the queue (get items until empty?)
    self.commands = None
    
    # Clean up: Clear responses dict; print warning if there are unfetched responses
    if self.responses:
      print "SerialInterface.run(): Warning: Terminated with unfetched response(s)"
      self.responses.clear()
    self.responses = None
    
    # Clean up: Close serial port
    if self.device is not None and self.device.isOpen():
      self.device.close()
      print "SerialInterface.run(): Serial port closed"
  
  def sendLoop(self, block=True):
    """Monitor queue for commands and send them until signaled to quit."""
    print "SerialInterface.sendLoop(): [SEND] loop starting..."
    while self.live:
      try:
        (id, command) = self.commands.get(block)  # block=True waits indefinitely for next command
        if command == "quit":  # special "quit" command breaks out of loop
          self.live = False  # signal any other threads to quit as well
          break
        #print "[SEND] Command :", command
        self.send(id, command)
      except Queue_Empty:
        print "[SEND] Empty queue"
        pass  # if queue is empty (after timeout), simply loop back and wait for more commands
    print "SerialInterface.sendLoop(): [SEND] loop terminated."
  
  def recvLoop(self):
    """Listen for responses and collect them in internal dict."""
    
    print "SerialInterface.recvLoop(): [RECV] loop starting..."
    while self.live:
      try:
        response = self.recv()
        if response is None:  # None response means something went wrong, break out of loop
          print "[RECV] No response"
          break
        else:
          #print "[RECV] Response:", response
          self.responses[response.get('id', -1)] = response  # store response by id for later retrieval, default id: -1
      except Exception as e:
        print "[RECV] Error:", e
    print "SerialInterface.sendLoop(): [RECV] loop terminated."
  
  def execLoop(self, block=True):
    """Combine functions of sendLoop() and recvLoop() to enforce sequential command execution."""
    print "SerialInterface.execLoop(): [EXEC] loop starting..."
    while self.live:
      try:
        (id, command) = self.commands.get(block)  # block=True waits indefinitely for next command
        if command == "quit":  # special "quit" command breaks out of loop
          self.live = False  # signal any other threads to quit as well
          break
        self.execute(id, command)
      except Queue_Empty:
        print "[EXEC] Empty queue"
        pass  # if queue is empty (after timeout), simply loop back and wait for more commands
    print "SerialInterface.execLoop(): [EXEC] loop terminated."
  
  def send(self, id, command):
    """Send a command, adding terminating EOL char(s)."""
    try:
      if prefix_id:
        self.device.write(str(id) + ' ') # TODO add id in the command message itself so that response can be mapped back
      self.device.write(command + command_eol)  # add EOL char(s)
      return True
    except Exception as e:
      print "SerialInterface.send(): Error:", e
      return False
  
  def recv(self):
    """Receive a newline-terminated response, and return it as a dict."""
    try:
      responseStr = self.device.readline()  # NOTE response must be \n terminated
      responseStr = responseStr.strip()  # strip EOL
      if len(responseStr) == 0:
        "SerialInterface.recv(): Warning: Blank response (timeout?)"
        return { }  # return a blank dict
      else:
        response = json.loads(responseStr)
        return response  # return dict representation of JSON object
    except Exception as e:
      print "SerialInterface.recv(): Error:", e
      return None
  
  def execute(self, id, command):
    """Send a command, wait for response and store it in dict."""
    try:
      self.send(id, command)
      response = self.recv()
      if response is None:  # None response means something went wrong
        print "[EXEC] No response"
      else:
        self.responses[response.get('id', id)] = response  # store response by id for later retrieval, default id: as passed in
    except Exception as e:
      print "[EXEC] Error:", e
  
  def fakeSend(self, id, command):
    if prefix_id:
      command = str(id) + ' ' + command
    print "[FAKE-SEND] {command}".format(command=command)
    sleep(fake_delay)
    return True
  
  def fakeRecv(self):
    sleep(fake_delay)
    response = { 'result': True, 'msg': "" }
    print "[FAKE-RECV] {response}".format(response=response)
    return response


class SerialCommand:
  """Exposes a set of methods for sending different navigation, action and sensor commands via a SerialInterface."""
  
  def __init__(self, commands, responses):
    self.commands = commands   # shared Queue
    self.responses = responses  # shared dict
  
  def putCommand(self, command):  # priority=0
    """Add command to queue, assigning a unique identifier."""
    id = random.randrange(sys.maxint)  # generate unique command id; TODO if id is sent to motor-control, make sure it is in range
    self.commands.put((id, command))  # insert command into queue as 2-tuple (id, command)
    # TODO insert into appropriate queue by priority?
    return id  # return id
  
  def getResponse(self, id, block=True):
    """Get response for given id from responses dict and return."""
    if block:
      while not id in self.responses:
        pass  # if blocking, wait till command has been serviced
    elif not id in self.responses:
      return None  # if non-blocking and command hasn't been serviced, return None
    
    response = self.responses.pop(id)  # get response and remove it
    return response
  
  def runCommand(self, command):
    """Add command to queue, block for response and return it."""
    id = self.putCommand(command)
    response = self.getResponse(id)
    return response
  
  def quit(self):
    """Terminate threads and quit."""
    self.putCommand("quit")  # special command "quit" is not serviced, it simply terminates the send and receive thread(s)
  
  def botStop(self):
    """Stop immediately."""
    response = self.runCommand("stop")  # TODO use putCommand() to make "stop" an immediate command (with no response)
    return response.get('result', False)
  
  def botSetSpeed(self, left, right):
    """Set individual wheel/side speeds (units: PWM values 0 - 10000)."""
    response = self.runCommand("pwm_drive {left} {right}".format(left=left, right=right))  # TODO use putCommand() [see botStop()]
    return response.get('result', False)
  
  def botMove(self, distance, speed=default_speed):
    response = self.runCommand("move {speed} {distance}".format(speed=speed, distance=distance))
    return int(response.get('distance', 0))
  
  def botTurnAbs(self, angle):
    response = self.runCommand("turn_abs {angle}".format(angle=int(angle * 10.0)))  # angle is 10ths of a degree
    return float(response.get('absHeading', 0)) / 10.0  # TODO make 10.0 factor a parameter
  
  def botTurnRel(self, angle):
    response = self.runCommand("turn_rel {angle}".format(angle=int(angle * 10.0)))  # angle is 10ths of a degree
    return float(response.get('relHeading', 0)) / 10.0  # TODO make 10.0 factor a parameter
  
  def armSetAngle(self, arm, angle, ramp=default_servo_ramp):
    response = self.runCommand("servo {channel} {ramp} {angle}".format(channel=arm, ramp=ramp, angle=angle))
    sleep(servo_delay)  # wait here for servo to reach angle
    return response.get('result', False)
  
  def armUp(self, arm):
    return self.armSetAngle(arm, arm_angles[arm][0])
  
  def armDown(self, arm):
    return self.armSetAngle(arm, arm_angles[arm][1])
  
  def gripperSetAngle(self, arm, angle, ramp=default_servo_ramp):
    response = self.runCommand("servo {channel} {ramp} {angle}".format(channel=grippers[arm], ramp=ramp, angle=angle))
    sleep(servo_delay)  # wait here for servo to reach angle
    return response.get('result', False)
  
  def gripperOpen(self, arm):
    gripper = grippers[arm]
    return self.gripperSetAngle(gripper, gripper_angles[gripper][0])
  
  def gripperClose(self, arm):
    gripper = grippers[arm]
    return self.gripperSetAngle(gripper, gripper_angles[gripper][1])
  
  def getAllSensorData(self):
    return self.runCommand("sensors")  # return the entire dict full of sensor data
  
  def getSensorData(self, sensorId):
    """Fetches current value of a sensor. Handles only scalar sensors, i.e. ones that return a single int value."""
    response = self.runCommand("sensor {sensorId}".format(sensorId=sensorId))
    # TODO timestamp sensor data here?
    return int(response.get('data', -1))  # NOTE this only handles single-value data
  
  def getSensorDataByName(self, sensorName):
    sensorId = sensors.get(sensorName, None)
    if sensorId is not None:
      return self.getSensorValue(sensorId)
    else:
      return -1
  
  # TODO write specialized sensor value fetchers for non-scalar sensors like the accelerometer (and possibly other sensors for convenience)


def main():
  """
  Standalone testing program for SerialInterface.
  Usage:
    python serial_interface.py [port [baudrate [timeout]]]
  """
  # Parameters
  port = default_port
  baudrate = default_baudrate
  timeout = default_timeout
  
  if len(sys.argv) > 1:
    port = sys.argv[1]
    if len(sys.argv) > 2:
      baudrate = int(sys.argv[2])
      if len(sys.argv) > 3:
        timeout = None if sys.argv[3] == "None" else float(sys.argv[3])
  
  # Serial interface
  print "main(): Creating SerialInterface(port=\"{port}\", baudrate={baudrate}, timeout={timeout}) process...".format(port=port, baudrate=baudrate, timeout=(-1 if timeout is None else timeout))
  
  #manager = Manager()  # manager service to share data across processes; NOTE must on Windows
  #si_commands = Queue(default_queue_maxsize)  # queue to store commands, process-safe; NOTE must on Windows
  #si_responses = manager.dict()  # shared dict to store responses, process-safe; NOTE must on Windows
  #si = SerialInterface(port, baudrate, timeout, si_commands, si_responses)  # NOTE commands and responses need not be passed in (other than in Windows?); SerialInterface creates its own otherwise
  si = SerialInterface(port, baudrate, timeout)
  si.start()
  
  # Serial command(s): Wrappers for serial interface
  sc1 = SerialCommand(si.commands, si.responses)  # pass in shared commands and responses structures to create a SerialCommand wrapper object
  # NOTE pass this SerialCommand object to anything that needs to call high-level methods (botMove, botTurn*, getSensorData, etc.)
  sc2 = SerialCommand(si.commands, si.responses) # multiple SerialCommand objects can be created if needed; the underlying SerialInterface data structures are process- and thread- safe
  
  # Test sequence, non-interactive
  print "main(): Starting test sequence...\n"
  sc1.botStop()
  pTest = Process(target=test.testPoly, args=(sc1,))
  pTest.start()  # start test process
  
  # Interactive session
  print "main(): Starting interactive session [Ctrl+D or \"quit\" to end]...\n"
  while True:
    try:
      command = raw_input("Me    > ")  # input command from user
    except EOFError:
      command = "quit"
    
    if command == "quit":
      print "\nmain(): Quiting interactive session..."
      break
    
    response = sc2.runCommand(command)  # equiv. to putCommand()..getResponse()
    #id = sc2.putCommand(command)
    #response = sc2.getResponse(id)
    print "Device: {response}".format(response=response)
  print "main(): Interactive session terminated."
  
  # Clean-up
  sc1.botStop()  # stop bot, if moving
  pTest.join()  # wait for test process to join
  print "main(): Test sequence terminated."
  
  # Wait for SerialInterface to terminate
  sc2.quit()
  si.join()
  print "main(): Done."


if __name__ == "__main__":
  main()
