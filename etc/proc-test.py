"""Experiments with multiprocessing."""

import os
from time import sleep
from multiprocessing import Process, Pipe

class Server:
  def __init__(self):
    print "Server.__init__()"
  
  def start(self):
    print "Server.start()"
    # TODO start listening for client requests, spawn a worker process on getting a request


class WorkerProcess(Process):
  def __init__(self, pipe):
    self.pipe = pipe
    #print "WorkerProcess.__init__()"
    Process.__init__(self)
  
  def run(self):
    print "WorkerProcess.run(): [{pid}] ppid = {ppid}".format(pid=self.pid, ppid=os.getppid())
    self.live = True
    while self.live:
      command = self.pipe.recv_bytes()
      result = self.execCommand(command)
      self.pipe.send_bytes(result)
    print "WorkerProcess.run(): [{pid}] Done.".format(pid=self.pid)
    self.pipe.close()
  
  def execCommand(self, command):
    #print "WorkerProcess.execCommand(): [{pid}] Command: {command}".format(pid=self.pid, command=command)
    if command == "quit":
      self.live = False
      return "OK Bye"
    return "OK"
  
  def test(self):
    print "WorkerProcess.test(): [{pid}] OS pid = {ospid}".format(pid=self.pid, ospid=os.getpid())
  
  #def __del__(self):
  #  print "WorkerProcess.__del__(): [{pid}]".format(pid=self.pid)
  


def main():
  print "main(): pid = {pid}, ppid = {ppid}".format(pid=os.getpid(), ppid=os.getppid())
  
  print "main(): Starting processes..."
  pipeToProc, pipeToMain = Pipe()
  proc = WorkerProcess(pipeToMain)
  proc.start()
  
  sleep(1)  # wait a bit to flush out all messages from child processes
  while proc.is_alive():
    proc.test()
    command = raw_input("main(): Command : ")
    if proc.is_alive():
      pipeToProc.send_bytes(command)
      print "main(): Response: {0}".format(pipeToProc.recv_bytes())
    else:
      print "main(): Oops! Process already died."
  
  print "main(): Done; joining on processes..."
  proc.join()


if __name__ == "__main__":
  main()
