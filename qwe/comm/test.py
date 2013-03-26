import sys
from multiprocessing import Process, Queue, Manager
import serial_interface

def testPoly(sc, numSides=4, sideLength=1000, dir=1):
  turnAngle = dir * 360 / numSides
  
  for i in range(numSides):
    print "testPoly(): Command : botMove({0})".format(sideLength)
    response = sc.botMove(sideLength)
    print "testPoly(): Response: {0}".format(response)
    
    print "testPoly(): Command : botTurnRel({0})".format(turnAngle)
    response = sc.botTurnRel(turnAngle)
    print "testPoly(): Response: {0}".format(response)


def testArm(sc, arm):
  print "testArm(): Command : armUp({0})".format(arm)
  response = sc.armUp(arm)
  print "testArm(): Response: {0}".format(response)
  
  print "testArm(): Command : armDown({0})".format(arm)
  response = sc.armDown(arm)
  print "testArm(): Response: {0}".format(response)


def main():
  port = serial_interface.default_port
  baudrate = serial_interface.default_baudrate
  timeout = serial_interface.default_timeout
  
  if len(sys.argv) > 1:
    port = sys.argv[1]
    if len(sys.argv) > 2:
      baudrate = int(sys.argv[2])
      if len(sys.argv) > 3:
        timeout = None if sys.argv[3] == "None" else float(sys.argv[3])
  
  print "main(): Creating SerialInterface(port=\"{port}\", baudrate={baudrate}, timeout={timeout})".format(port=port, baudrate=baudrate, timeout=(-1 if timeout is None else timeout))
  si_commands = Queue(serial_interface.default_queue_maxsize)  # queue to store commands, process-safe; NOTE Windows-only
  manager = Manager()  # manager service to share data across processes; NOTE Windows-only
  si_responses = manager.dict()  # shared dict to store responses, process-safe; NOTE Windows-only
  si = SerialInterface(port, baudrate, timeout, si_commands, si_responses)  # NOTE commands and responses need to be passed in on Windows only; SerialInterface creates its own otherwise
  si.start()
  
  sc = SerialCommand(si)
  
  # Test suite
  sc.botStop()
  testPoly(sc, 4)
  sc.botStop()
  testArm(sc, serial_interface.left_arm)
  sc.botStop()
  testArm(sc, serial_interface.right_arm)
  sc.botStop()
  
  sc.quit()
  sc.join()
  print "main(): Done."

if __name__ == "__main__":
  main()