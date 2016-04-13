from Adafruit_PWM_Servo_Driver import PWM
import time
import signal
import sys
import math
import RPi.GPIO as GPIO
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
    GPIO.cleanup()
    sys.exit(0)
signal.signal(signal.SIGINT, int_handler)

test = True
servo = False

ds4 = None
pwm = None
pwma = None
pwmb = None

if (test):
    class test_dualshock4(object):
        def read(self):
            axis = [0] * 2
            axis[0] = input("x: ")
            axis[1] = input("y: ")
            return axis
    ds4 = test_dualshock4()
else:
    ds4 = dualshock4('/dev/hidraw0')

if (servo):
    pwm = PWM(0x40)
    pwm.setPWMFreq(200)
else:
    GPIO.setmode(GPIO.BOARD)
    channels = [7, 11, 13, 15, 12, 16, 18]
    # STBY PWMB BIN2 BIN1 AIN1 AIN2 PWMA
    GPIO.setup(channels, GPIO.OUT)
    GPIO.output(channels, GPIO.LOW)
    pwma = GPIO.PWM(18, 120)
    pwma.start(0)
    pwmb = GPIO.PWM(11, 120)
    pwmb.start(0)

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
    engine_l_dir = 0
    engine_r_dir = 0
    if (engine_l):
        engine_l_dir = int(math.fabs(engine_l) / engine_l)
        engine_l = math.fabs(engine_l)
    if (engine_r):
        engine_r_dir = int(math.fabs(engine_r) / engine_r)
        engine_r = math.fabs(engine_r)
    
    if (x < 0):
        temp = engine_l
        engine_l = engine_r
        engine_r = temp

    print('X = %d, Y = %d, Left = %d, Right = %d' % (x, y, engine_l, engine_r))
    if (servo):
        engine_l = engine_l / 120 * engine_l_dir * 0.5 + 1.5
        engine_r = engine_r / 120 * engine_r_dir * 0.5 + 1.5
        setServoPulse(4, engine_l)
        setServoPulse(5, engine_r)
    else:
        if (velocity):
            GPIO.output(7, GPIO.LOW)
        else:
            if (engine_l_dir):
                if (engine_l_dir > 0):
                    # AIN1 L AIN2 H CCW
                    GPIO.output(12, GPIO.LOW)
                    GPIO.output(16, GPIO.HIGH)
                else:
                    # AIN1 H AIN2 L CW
                    GPIO.output(12, GPIO.HIGH)
                    GPIO.output(16, GPIO.LOW)
                pwma.ChangeDutyCycle(engine_l / 120)
            else:
                # AIN1 L AIN2 L STOP
                GPIO.output(12, GPIO.LOW)
                GPIO.output(16, GPIO.LOW)
            
            if (engine_r_dir):
                if (engine_r_dir > 0):
                    # BIN1 H BIN2 L CW
                    GPIO.output(15, GPIO.HIGH)
                    GPIO.output(13, GPIO.LOW)
                else:
                    # BIN1 L BIN2 H CCW
                    GPIO.output(15, GPIO.LOW)
                    GPIO.output(13, GPIO.HIGH)
                pwmb.ChangeDutyCycle(engine_r / 120)
            else:
                # BIN1 L BIN2 L STOP
                GPIO.output(15, GPIO.LOW)
                GPIO.output(13, GPIO.LOW)
            GPIO.output(7, GPIO.HIGH)