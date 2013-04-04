import sys
import signal
from multiprocessing import Process, Queue, Manager
import comm.serial_interface

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
  
  # Set signal handlers
  live = True
  def handleSignal(signum, frame):
    if signum == signal.SIGTERM or signum == signal.SIGINT:
      print "handleSignal(): Termination signal ({0}); stopping comm loop...".format(signum)
    else:
      print "handleSignal(): Unknown signal ({0}); stopping comm loop anyways...".format(signum)
    #si.quit()
    live = False
  
  signal.signal(signal.SIGTERM, handleSignal)
  signal.signal(signal.SIGINT, handleSignal)
  
  # Sensor read loop
  ctr = 0
  while live and ctr < 100:
    ctr = ctr + 1
    sensorData = sc.getAllSensorData()
    print "main(): Sensor data: {0}".format(str(sensorData))
  
  # Reset signal handlers to default behavior
  signal.signal(signal.SIGTERM, signal.SIG_DFL)
  signal.signal(signal.SIGINT, signal.SIG_DFL)
  
  sc.quit()
  si.join()
  print "main(): Done."

if __name__ == "__main__":
  main()