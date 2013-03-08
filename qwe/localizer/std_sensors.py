from numpy import pi
from sensors import Ultrasonic
from pose import Pose

# should go into a config file
sensor_noise = 0.25
sensors = []
sensors.append(Ultrasonic('F', Pose(0,0,0.0), sensor_noise))
sensors.append(Ultrasonic('L', Pose(0,0,pi/2), sensor_noise))
sensors.append(Ultrasonic('R', Pose(0,0,-pi/2), sensor_noise))
sensors.append(Ultrasonic('B', Pose(0,0,-pi), sensor_noise))

