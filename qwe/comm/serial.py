"""Communication module."""

class SerialInterface:
  defaultPort = "/dev/ttyO3"
  
  def __init__(self, port=defaultPort):
    self.port = port
    # TODO open serial port (and exchange hello messages?)
  
  def botMove(self, distance):
    pass  # TODO send move command, wait for completion ack, return actual distance traveled (relative)
  
  def botTurn(self, angle):
    pass  # TODO send turn command, wait for completion ack, return actual angle turned (relative)
  
  def armRotate(self, angle):
    pass  # TODO send arm rotate command, wait for completion ack, return actual arm angle (absolute?)
  
  def armDown(self):
    pass  # TODO rotate arm to lowest position (to pick-up blocks) [use armRotate], return True/False to indicate success/failure
  
  def armUp(self):
    pass  # TODO rotate arm to highest position (e.g. with block in gripper) [use armRotate], return True/False to indicate success/failure
  
  def gripperSet(self, value):
    pass  # TODO open gripper to specified value (distance.angle) and return True/False on completion
  
  def gripperClose(self):
    pass  # TODO close gripper (to grab) [use gripperSet] and return True/False on completion
  
  def gripperOpen(self):
    pass  # TODO open gripper (to release) [use gripperSet] and return True/False on completion
