"""Experiments with multiprocessing."""

import sys
import os
import random
from time import sleep
from multiprocessing import Process, Pipe, Manager, Lock, Value
from multiprocessing import Queue as MultiQueue # Process-shared Queue
import Queue # regular queue module
from ctypes import c_bool

class Server:
  def __init__(self):
    print "Server.__init__()"
  
  def start(self):
    print "Server.start()"
    # TODO start listening for client requests, spawn a worker process on getting a request


class PipedService(Process):
  def __init__(self, pipe):
    print "PipedService.__init__()"
    Process.__init__(self)
    self.pipe = pipe
    self.live = False
  
  def run(self):
    print "PipedService.run(): [{pid}] ppid = {ppid}".format(pid=self.pid, ppid=os.getppid())
    self.live = True
    while self.live:
      command = self.pipe.recv_bytes()
      result = self.execCommand(command)
      self.pipe.send_bytes(result)
    print "PipedService.run(): [{pid}] Done.".format(pid=self.pid)
    self.pipe.close()
  
  def execCommand(self, command):
    #print "PipedService.execCommand(): [{pid}] Command: {command}".format(pid=self.pid, command=command)
    if command == "quit":
      self.stop()
      return "OK Bye"
    return "OK"

  def stop(self):
    self.live = False
  
  def test(self):
    print "PipedService.test(): [{pid}] OS pid = {ospid}".format(pid=self.pid, ospid=os.getpid())
  
  #def __del__(self):
  #  print "PipedService.__del__(): [{pid}]".format(pid=self.pid)


class QueuedService(Process):
  def __init__(self):
    print "QueuedService.__init__()"
    Process.__init__(self)
    self.commands = MultiQueue(10)
    self.manager = Manager()
    self.responses = self.manager.dict()

  def run(self):
    print "QueuedService.run(): [{pid}] ppid = {ppid}...".format(pid=self.pid, ppid=os.getppid())
    self.loop()
    print "QueuedService.run(): [{pid}] Done.".format(pid=self.pid)

  def loop(self):
    """Main loop: Monitor queue for commands and service them until signaled to quit."""
    print "QueuedService.loop(): Starting main [LOOP]..."
    while True:
      try:
        (commandId, command) = self.commands.get(True, timeout=10)  # True blocks indefinitely
        #print "[LOOP] Command : {0}".format(command) # [debug]
        
        response = self.execCommand(command)
        if response is None:  # None response means something went wrong, break out of loop
          break
        elif response.startswith("ERROR"):
          print "[LOOP] Error response: " + response
          #response = "ERROR"  # modify response since it is useless anyways?

        #print "[LOOP] Response : {0}".format(response) # [debug]
        self.responses[commandId] = response  # store result by commandId for later retrieval
        #print "[LOOP] Responses: {0}".format(self.responses) # [debug]

        if command == "quit":  # special "quit" command breaks out of loop
          break
      except Queue.Empty:
        print "[LOOP] Empty queue"
        pass  # if queue is empty, simply loop back and wait for more commands

    print "QueuedService.loop(): Main [LOOP] terminated."
    
    # Clean up: Clear queue and responses dict (print warning if there are unserviced commands?)
    if not self.commands.empty():
      print "QueuedService.loop(): Warning: Terminated with pending commands"
      while not self.commands.empty():
        self.commands.get()
      # TODO find a better way to simply clear/flush the queue?
    self.responses.clear()
  
  def stop(self):
    """Stop main loop by sending quit command."""
    self.putCommand("quit")

  def execCommand(self, command):
    """Execute command."""
    #print "QueuedService.execCommand(): Command: {0}".format(command) # [debug]
    try:
      # fake sending command
      response = "OK" # fake getting a response
      #print "QueuedService.execCommand(): Response: {0}".format(response) # [debug]
      return response
    except Exception as e:
      print "QueuedService.execCommand(): Error:", e
      return None

  def putCommand(self, command):  # priority=0
    #print "QueuedService.putCommand(): Command: {0}".format(command) # [debug]
    commandId = random.randrange(sys.maxint)  # generate unique command ID
    self.commands.put((commandId, command))  # insert command into queue as 2-tuple (ID, command)
    #print "QueuedService.putCommand(): Command ID: {0}".format(commandId) # [debug]
    return commandId  # return ID
  
  def getResponse(self, commandId, block=True):
    #print "QueuedService.getResponse(): Command ID: {0}, block?: {1}".format(commandId, block) # [debug]
    response = self.responses.pop(commandId, None)  # get response and remove it
    if block:
      while response is None:
        #print "QueuedService.getResponse(): [BLOCK] No response yet for ID: {0}".format(commandId) # [debug]
        #print "QueuedService.getResponse(): [BLOCK] Responses: {0}".format(self.responses)
        #sleep(0.5) # TODO properly yield till we get something?
        response = self.responses.pop(commandId, None)  # keep trying till command has been serviced

    #print "QueuedService.getResponse(): Response: {0}".format(response) # [debug]
    return response  # if non-blocking and command hasn't been serviced, None will be returned
  
  def runCommandSync(self, command):
    """Convenience method for running a command and blocking for response."""
    #print "QueuedService.runCommandSync(): Command: {0}".format(command) # [debug]
    commandId = self.putCommand(command)
    response = self.getResponse(commandId)
    return response


class MultiPipedService(Process):
  def __init__(self):
    print "MultiPipedService.__init__()"
    Process.__init__(self)
    self.clientCount = 0
    self.clients = dict()  # { clientId: connection, ... }
    #self.manager = Manager()
    #self.clients = self.manager.dict()  # NOTE doesn't work as Connection objects cannot be stored in a Manager dict
    self.live = False

  def run(self):
    print "MultiPipedService.run(): [{pid}] ppid = {ppid}...".format(pid=self.pid, ppid=os.getppid())
    self.live = True
    self.loop()
    print "MultiPipedService.run(): [{pid}] Done.".format(pid=self.pid)

  def addClient(self):
    # Get a new client ID
    clientId = self.clientCount
    self.clientCount = self.clientCount + 1

    # Create a pipe, add one connection to clients dict
    clientConnection, myConnection = Pipe()
    self.clients[clientId] = myConnection

    # Return client ID and other connection (other end of the pipe) in a wrapped helper object
    return MultiPipedServiceHelper(clientId, clientConnection)

  def removeClient(self, clientId):
    # Pop client connection from dict and close it
    connection = self.clients.pop(clientId, None)
    if connection is not None:
      connection.close()

  def removeAllClients(self):
    for clientId in self.clients.keys():  # necessary to allow modification
      self.removeClient(clientId)

  def loop(self):
    """Main loop: Monitor pipes for commands and service them until signaled to quit."""
    print "MultiPipedService.loop(): Starting main [LOOP]..."
    while self.live:
      #try:
        #print "[LOOP] {0} clients".format(len(self.clients))
        # For each client connection
        for clientId, connection in self.clients.iteritems():
          #print "[LOOP] Checking client #{0}...".format(clientId)
          # Check if any request is available; if not, move on to next client
          if not connection.poll():  # NOTE with many clients, timeout can make things sluggish
            #print "[LOOP] No request from client #{0}".format(clientId)
            continue

          # Get requested command
          #print "[LOOP] Command available!"
          command = connection.recv_bytes()
          #print "[LOOP] Command :", command # [debug]

          # Execute command (send request) and retrieve response
          response = self.execCommand(command)
          if response is None:  # None response means something went wrong, break out of loop
            self.live = False
            break
          elif response.startswith("ERROR"):  # ERROR may mean the last command was erroneous
            print "[LOOP] Error response:", response
            #response = "ERROR"  # modify response since it is useless anyways?

          # Send back response
          #print "[LOOP] Response :", response # [debug]
          connection.send_bytes(response)

          # If this was a quit command, break out of loop (no further requests are serviced)
          if command == "quit":  # special "quit" command breaks out of loop
            self.live = False
            break
      #except Exception as e:
      #  print "[LOOP] Exception:", e

    print "MultiPipedService.loop(): Main [LOOP] terminated."
    
    # Clean up: Remove all clients
    self.removeAllClients()
  
  def stop(self):
    """Stop main loop."""
    self.live = False  # NOTE not thread/process-safe (make sel.live a managed object for that)

  def execCommand(self, command):
    """Execute command."""
    #print "MultiPipedService.execCommand(): Command: {0}".format(command) # [debug]
    try:
      # fake sending command
      response = "OK" # fake getting a response
      #print "MultiPipedService.execCommand(): Response: {0}".format(response) # [debug]
      return response
    except Exception as e:
      print "MultiPipedService.execCommand(): Error:", e
      return None


class MultiPipedServiceHelper:
  def __init__(self, id, connection):
    self.id = id
    self.connection = connection

  def runCommandSync(self, command):
    self.connection.send_bytes(command)
    if not self.connection.poll(5):  # NOTE make timeout a named parameter
      return None
    return self.connection.recv_bytes()
    # TODO write convenience methods to convert commands to strings
    # TODO convert JSON responses back to Python objects
    # TODO handle exceptions (e.g. connection is closed, error response)


class SynchronizedService(Process):
  def __init__(self):
    print "SynchronizedService.__init__()"
    Process.__init__(self)
    self.lock = Lock()
    self.live = Value(c_bool, False, lock=True)
  
  def run(self):
    print "SynchronizedService.run(): [{pid}] ppid = {ppid}...".format(pid=self.pid, ppid=os.getppid())
    self.live.value = True
    self.loop()
    print "SynchronizedService.run(): [{pid}] Done.".format(pid=self.pid)
  
  def loop(self):
    while self.live.value:
      sleep(5)  # nothing to do
  
  def stop(self):
    """Stop main loop."""
    self.live.value = False  # NOTE not thread/process-safe (make sel.live a managed object for that)
  
  def execCommand(self, command):
    """Execute command."""
    #print "SynchronizedService.execCommand(): Command: {0}".format(command) # [debug]
    try:
      if self.live.value:
        # fake sending command
        response = "OK" # fake getting a response
        #print "SynchronizedService.execCommand(): Response: {0}".format(response) # [debug]
        if command == "quit":
          self.live.value = False
        return response
      else:
        raise Exception("Process no longer alive!")
    except Exception as e:
      print "SynchronizedService.execCommand(): Error:", e
      return None
  
  def runCommandSync(self, command):
    self.lock.acquire()
    response = self.execCommand(command)
    self.lock.release()
    return response


def main(which="PipedService"):
  print "main(): pid = {pid}, ppid = {ppid}".format(pid=os.getpid(), ppid=os.getppid())

  if which == "PipedService":
    print "main(): Starting PipedService process..."
    pipeToProc, pipeToMain = Pipe()
    proc = PipedService(pipeToMain)
    proc.start()
    
    sleep(1)  # [debug] wait a bit to flush out all messages from child processes
    proc.test()  # [debug] test self and parent PIDs
    while proc.is_alive():
      command = raw_input("main(): Command : ")
      if proc.is_alive():
        pipeToProc.send_bytes(command)
        print "main(): Response: {0}".format(pipeToProc.recv_bytes())
      else:
        print "main(): Oops! Process already died."

    print "main(): Done; joining on process(es)..."
    proc.join()
  elif which == "QueuedService":
    print "main(): Starting QueuedService child process..."
    service = QueuedService()
    service.start()
    
    print "main(): Starting cannedLoop() child process..."
    cannedCommands = ["Hi", "How", "is", "it going?", "quit"]
    pCannedLoop = Process(target=cannedLoop, args=(service, cannedCommands, 5))
    pCannedLoop.start()

    print "main(): Starting interactiveLoop() (NOTE: Not a child process)..."
    interactiveLoop(service)
    
    print "main(): Joining on process(es)..."
    pCannedLoop.join()
    service.join()
    print "main(): Done."
  elif which == "MultiPipedService":
    print "main(): Starting MultiPipedService child process..."
    service = MultiPipedService()
    serviceHelper1 = service.addClient()
    serviceHelper2 = service.addClient()
    service.start()  # NOTE must addClient()s before calling start()
    
    sleep(1)  # let other process start-up messages to pass through
    print "main(): Starting cannedLoop() child process..."
    cannedCommands = ["Hi", "How", "is", "it going?", "quit"]
    pCannedLoop = Process(target=cannedLoop, args=(serviceHelper1, cannedCommands, 2))
    pCannedLoop.start()

    sleep(1)  # let other process start-up messages to pass through
    print "main(): Starting interactive loop..."
    while True:
      command = raw_input("Command > ")
      if not service.is_alive():
        print "main(): Oops! Service already dead; aborting..."
        break
      response = serviceHelper2.runCommandSync(command)
      print "Response: {0}".format(response)
      if command == "quit":
        break
    print "main(): Interactive loop terminated."
    
    print "main(): Joining on process(es)..."
    pCannedLoop.join()
    service.join()  # MultiPipedService automatically closes client connections on quit
    print "main(): Done."
  elif which == "SynchronizedService":
    print "main(): Starting SynchronizedService child process..."
    service = SynchronizedService()
    service.start()
    
    sleep(1)  # let other process start-up messages to pass through
    print "main(): Starting cannedLoop() child process..."
    cannedCommands = ["Hi", "How", "is", "it going?", "quit"]
    pCannedLoop = Process(target=cannedLoop, args=(service, cannedCommands, 2))
    pCannedLoop.start()

    sleep(1)  # let other process start-up messages to pass through
    print "main(): Starting interactive loop..."
    while True:
      command = raw_input("Command > ")
      if not service.is_alive():
        print "main(): Oops! Service already dead; aborting..."
        break
      response = service.runCommandSync(command)
      print "Response: {0}".format(response)
      if command == "quit":
        break
    print "main(): Interactive loop terminated."
    
    print "main(): Joining on process(es)..."
    pCannedLoop.join()
    service.join()  # MultiPipedService automatically closes client connections on quit
    print "main(): Done."
  else:
    print "main(): Unknown service type \"{0}\"".format(which)

def interactiveLoop(service):
  print "interactiveLoop(): Starting command loop..."
  while service.is_alive():  # NOTE this can only be done if service is a child process of this (calling) process
    command = raw_input("Command > ")
    if service.is_alive():
      if command == "quit":
        service.stop()
        break
      else:
        response = service.runCommandSync(command)
        print "Response: {0}".format(response)
    else:
      print "interactiveLoop(): Oops! Service down; aborting..."
      break
  print "interactiveLoop(): Done."

def cannedLoop(service, commands, pause=1.0):
  print "cannedLoop(): Starting command loop..."
  for command in commands:
    print "Command : {0}".format(command)
    response = service.runCommandSync(command)
    print "Response: {0}".format(response)
    sleep(pause)  # pause to give any interactive loop enough time
  print "cannedLoop(): Done."

if __name__ == "__main__":
  serviceType = sys.argv[1] if len(sys.argv) > 1 else "PipedService"
  main(serviceType)
