from numpy import pi
from sensors import Ultrasonic
from pose import Pose

# datasheets say resolution is within 0.1"
# need to figure out how this translates to gaussian std dev
sensor_noise = 0.05  # 2 std devs = resolution, so 95% of readings within resolution
sensors = []
sensors.append(Ultrasonic('F', Pose(4.0,0,0.0), sensor_noise))
sensors.append(Ultrasonic('L', Pose(0.0,-4.0,pi/2), sensor_noise))
sensors.append(Ultrasonic('R', Pose(0.0,4.0,-pi/2), sensor_noise))
sensors.append(Ultrasonic('B', Pose(-4.0,0,-pi), sensor_noise))

