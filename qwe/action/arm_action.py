"""
Arm logic - executes a series of comm's arm commands.
"""


def getBlock(armId):
    SerialInterface.gripperOpen(armId)
    SerialInterface.armDown(armId)
    SerialInterface.gripperClose(armId)
    SerialInterface.armUp(armId)
    
def placeBlock(armId):
    SerialInterface.armDown(armId)
    SerialInterface.gripperOpen(armId)
    SerialInterface.armUp(armId)
    SerialInterface.gripperClose(armId)

