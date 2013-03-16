import sys
import serial_interface as si

def testPoly(serialInterface, numSides=4, sideLength=1000, dir=1):
  turnAngle = dir * 360 / numSides
  
  for i in range(numSides):
    print "testPoly(): Command : botMove({0})".format(sideLength)
    response = serialInterface.botMove(sideLength)
    print "testPoly(): Response: {0}".format(response)
    
    print "testPoly(): Command : botTurn({0})".format(turnAngle)
    response = serialInterface.botTurn(turnAngle)
    print "testPoly(): Response: {0}".format(response)


def testArm(serialInterface, arm):
  print "testArm(): Command : armUp({0})".format(arm)
  response = serialInterface.armUp(arm)
  print "testArm(): Response: {0}".format(response)
  
  print "testArm(): Command : armDown({0})".format(arm)
  response = serialInterface.armDown(arm)
  print "testArm(): Response: {0}".format(response)


def main():
  port = si.default_port
  baudrate = si.default_baudrate
  timeout = si.default_timeout
  
  if len(sys.argv) > 1:
    port = sys.argv[1]
    if len(sys.argv) > 2:
      baudrate = int(sys.argv[2])
      if len(sys.argv) > 3:
        timeout = None if sys.argv[3] == "None" else float(sys.argv[3])
  
  print "main(): Creating SerialInterface(port=\"{port}\", baudrate={baudrate}, timeout={timeout})".format(port=port, baudrate=baudrate, timeout=(-1 if timeout is None else timeout))
  serialInterface = si.SerialInterface(port, baudrate, timeout)
  if not serialInterface.start():
    return
  
  # Test suite
  serialInterface.botStop()
  testPoly(serialInterface, 4)
  serialInterface.botStop()
  testArm(serialInterface, si.left_arm)
  serialInterface.botStop()
  testArm(serialInterface, si.right_arm)
  serialInterface.botStop()
  
  serialInterface.stop()
  print "main(): Done."

if __name__ == "__main__":
  main()