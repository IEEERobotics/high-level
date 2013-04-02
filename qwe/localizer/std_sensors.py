from numpy import pi
from sensors import Ultrasonic
from pose import Pose

# datasheets say resolution is within 0.1"
# need to figure out how this translates to gaussian std dev
ultra_noise = 0.05  # 2 std devs = resolution, so 95% of readings within resolution

centered_str = {}
centered_str['front'] = Ultrasonic('front', Pose(0.0,0,0.0), ultra_noise)
centered_str['left'] = Ultrasonic('left', Pose(0.0,0.0,pi/2), ultra_noise)
centered_str['right'] = Ultrasonic('right', Pose(0.0,0.0,-pi/2), ultra_noise)
centered_str['back'] = Ultrasonic('back', Pose(0.0,0.0,-pi), ultra_noise)

centered_cone = {}
centered_cone['front'] = Ultrasonic('front', Pose(0.0,0,0.0), ultra_noise, cone=True)
centered_cone['left'] = Ultrasonic('left', Pose(0.0,0.0,pi/2), ultra_noise, cone=True)
centered_cone['right'] = Ultrasonic('right', Pose(0.0,0.0,-pi/2), ultra_noise, cone=True)
centered_cone['back'] = Ultrasonic('back', Pose(0.0,0.0,-pi), ultra_noise, cone=True)

offset_str = {}
offset_str['front'] = Ultrasonic('front', Pose(0.0,8.4,0.0), ultra_noise)
offset_str['left'] = Ultrasonic('left', Pose(-5.0,3.4,pi/2), ultra_noise)
offset_str['right'] = Ultrasonic('right', Pose(5.0,3.4,-pi/2), ultra_noise)
offset_str['back'] = Ultrasonic('back', Pose(0.0,-1.6,-pi), ultra_noise)

offset_cone = {}
offset_cone['front'] = Ultrasonic('front', Pose(0.0,8.4,0.0), ultra_noise, cone=True)
offset_cone['left'] = Ultrasonic('left', Pose(-5.0,3.4,pi/2), ultra_noise, cone=True)
offset_cone['right'] = Ultrasonic('right', Pose(5.0,3.4,-pi/2), ultra_noise, cone=True)
offset_cone['back'] = Ultrasonic('back', Pose(0.0,-1.6,-pi), ultra_noise, cone=True)

default = offset_cone
