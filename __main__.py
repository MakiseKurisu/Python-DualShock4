from Adafruit_PWM_Servo_Driver import PWM
import time
import signal
import sys
import dualshock4

def setServoPulse(channel, pulse):
    pulseLength = 1000000                   # 1,000,000 us per second
    pulseLength /= 200                       # 200 Hz
    #print("%d us per period" % pulseLength)
    pulseLength /= 4096                     # 12 bits of resolution
    #print("%d us per bit" % pulseLength)
    pulse *= 1000
    pulse /= pulseLength
    pwm.setPWM(channel, 0, pulse)

def int_handler(signal, frame):
    pwm = PWM(0x40)
    pwm.setAllPWM(0, 0)
    sys.exit(0)
signal.signal(signal.SIGINT, int_handler)

ds4 = dualshock4('/dev/hidraw0')

pwm = PWM(0x40)
pwm.setPWMFreq(200)

servo = True

while True:
    axis = ds4.read()
    x = axis[0]
    y = axis[1]

    velocity = math.hypot(x, y)
    if (velocity > 120):
        velocity = 120
    
    if (y == 0):
        engine_l = velocity
        engine_r = -1 * velocity
    else:
        engine_l = math.fabs(y) / y * velocity
        theta = (2 * math.atan(math.fabs(x) / y)) % math.pi
        engine_r = math.cos(theta) * velocity
    
    if (x < 0):
        temp = engine_l
        engine_l = engine_r
        engine_r = temp
    
    if (servo):
        engine_l = engine_l / 120 * 0.5 + 1.5
        engine_r = engine_r / 120 * 0.5 + 1.5
        setServoPulse(4, engine_l)
        setServoPulse(5, engine_r)
        print('X = %d, Y = %d, Left = %d, Right = %d' % (x, y, engine_l, engine_r))
    else:
        print('X = %d, Y = %d, Left = %d, Right = %d' % (x, y, engine_l, engine_r))