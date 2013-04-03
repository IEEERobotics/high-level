import sys
from multiprocessing import Process, Queue, Manager
import comm.serial_interface

do_test_move = False
do_test_arm = True

def testPoly(sc, numSides=4, sideLength=1000, dir=1):
  turnAngle = 10 * dir * 360 / numSides  # angle must be sent in 10ths of a degree
  
  for i in range(numSides):
    print "testPoly(): Command : botMove({0})".format(sideLength)
    response = sc.botMove(sideLength)
    print "testPoly(): Response: {0}".format(response)
    
    print "testPoly(): Command : botTurnRel({0})".format(turnAngle)
    response = sc.botTurnRel(turnAngle)
    print "testPoly(): Response: {0}".format(response)


def testArm(sc, arm):
  print "testArm(): Command : armDown({0})".format(arm)
  response = sc.armDown(arm)
  print "testArm(): Response: {0}".format(response)
  
  print "testArm(): Command : gripperOpen({0})".format(arm)
  response = sc.gripperOpen(arm)
  print "testArm(): Response: {0}".format(response)
  
  print "testArm(): Command : gripperClose({0})".format(arm)
  response = sc.gripperClose(arm)
  print "testArm(): Response: {0}".format(response)
  
  print "testArm(): Command : armUp({0})".format(arm)
  response = sc.armUp(arm)
  print "testArm(): Response: {0}".format(response)


def main():
  port = comm.serial_interface.default_port
  baudrate = comm.serial_interface.default_baudrate
  timeout = comm.serial_interface.default_timeout
  
  if len(sys.argv) > 1:
    port = sys.argv[1]
    if len(sys.argv) > 2:
      baudrate = int(sys.argv[2])
      if len(sys.argv) > 3:
        timeout = None if sys.argv[3] == "None" else float(sys.argv[3])
  
  print "main(): Creating SerialInterface(port=\"{port}\", baudrate={baudrate}, timeout={timeout})".format(port=port, baudrate=baudrate, timeout=(-1 if timeout is None else timeout))
  si_commands = Queue(comm.serial_interface.default_queue_maxsize)  # queue to store commands, process-safe; NOTE Windows-only
  manager = Manager()  # manager service to share data across processes; NOTE Windows-only
  si_responses = manager.dict()  # shared dict to store responses, process-safe; NOTE Windows-only
  si = comm.serial_interface.SerialInterface(port, baudrate, timeout, si_commands, si_responses)  # NOTE commands and responses need to be passed in on Windows only; SerialInterface creates its own otherwise
  si.start()
  
  sc = comm.serial_interface.SerialCommand(si.commands, si.responses)
  
  # Test suite
  sc.botStop()

  if do_test_move:
    testPoly(sc, 4)
    sc.botStop()

  if do_test_arm:
    testArm(sc, comm.serial_interface.left_arm)
    sc.botStop()
    testArm(sc, comm.serial_interface.right_arm)
    sc.botStop()
  
  sc.quit()
  si.join()
  print "main(): Done."

if __name__ == "__main__":
  main()