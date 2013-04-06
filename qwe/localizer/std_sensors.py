from numpy import pi
from sensors import Ultrasonic, Compass
from pose import Pose

# datasheets say resolution is within 0.1"
# need to figure out how this translates to gaussian std dev
ultra_noise = 0.05  # 2 std devs = resolution, so 95% of readings within resolution
compass_noise = 0.017  # roughly 0.1 degrees

compass_only = {}
compass_only['heading'] = Compass('heading', compass_noise)

centered_str = {}
centered_str['front'] = Ultrasonic('front', Pose(0.0,0,0.0), ultra_noise)
centered_str['left'] = Ultrasonic('left', Pose(0.0,0.0,pi/2), ultra_noise)
centered_str['right'] = Ultrasonic('right', Pose(0.0,0.0,-pi/2), ultra_noise)
centered_str['back'] = Ultrasonic('back', Pose(0.0,0.0,-pi), ultra_noise)
centered_str['heading'] = Compass('heading', compass_noise)

centered_cone = {}
centered_cone['front'] = Ultrasonic('front', Pose(0.0,0,0.0), ultra_noise, cone=True)
centered_cone['left'] = Ultrasonic('left', Pose(0.0,0.0,pi/2), ultra_noise, cone=True)
centered_cone['right'] = Ultrasonic('right', Pose(0.0,0.0,-pi/2), ultra_noise, cone=True)
centered_cone['back'] = Ultrasonic('back', Pose(0.0,0.0,-pi), ultra_noise, cone=True)

offset_str = {}
offset_str['front'] = Ultrasonic('front', Pose(+8.4,0.0,0.0), ultra_noise, failure = 0)
offset_str['left'] = Ultrasonic('left', Pose(+3.4,5.0,pi/2), ultra_noise, failure = 0)
offset_str['right'] = Ultrasonic('right', Pose(+3.4,-5.0,-pi/2), ultra_noise, failure = 0)
offset_str['back'] = Ultrasonic('back', Pose(-1.6,0.0,-pi), ultra_noise, failure = 0)
offset_str['heading'] = Compass('heading', compass_noise)

default = offset_str
#default = compass_only
