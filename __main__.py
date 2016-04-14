from Adafruit_PWM_Servo_Driver import PWM
import time
import signal
import sys
import math
import RPi.GPIO as GPIO
from ds4 import dualshock4
import ptvsd

ptvsd.enable_attach('test')

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

test = False
servo = False

ds4 = None
pwm = None
pwma = None
pwmb = None

if (test):
    class test_dualshock4(object):
        def read(self):
            axis = [0] * 2
            try:
                axis[0] = int(float(input("x: ")))
            except:
                axis[0] = 0
            try:
                axis[1] = int(float(input("y: ")))
            except:
                axis[1] = 0
            return axis
    ds4 = test_dualshock4()
else:
    ds4 = dualshock4('/dev/hidraw2')

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

    velocity = int(math.hypot(x, y))
    if (velocity > 120):
        velocity = 120
    
    theta = math.atan2(x,y)
    if (theta == 0):
        engine_l = engine_r = velocity
    elif (theta == math.pi):
        engine_l = engine_r = -1 * velocity
    else:
        if (theta > 0):
            if (theta <= (math.pi / 2)):
                engine_l = velocity
            else:
                engine_l = -1 * velocity
            theta = theta * 2
            if (theta >= math.pi):
                theta -= math.pi
            # engine_r = math.cos(theta) * velocity
            engine_r = (1 - theta * 2 / math.pi) * velocity
        else:
            if (theta >= -1 * (math.pi / 2)):
                engine_r = velocity
            else:
                engine_r = -1 * velocity
            theta = theta * 2
            if (theta <= -1 * math.pi):
                theta += math.pi
            # engine_l = math.cos(theta) * velocity
            engine_l = (1 + theta * 2 / math.pi) * velocity
    
    engine_l_dir = 0
    engine_r_dir = 0
    if (math.fabs(engine_l) < 0.1):
        engine_l = 0
    else:
        engine_l_dir = int(math.fabs(engine_l) / engine_l)
        engine_l = int(math.fabs(engine_l))
        if (engine_l > 120):
            engine_l = 120
    if (math.fabs(engine_r) < 0.1):
        engine_r = 0
    else:
        engine_r_dir = int(math.fabs(engine_r) / engine_r)
        engine_r = int(math.fabs(engine_r))
        if (engine_l > 120):
            engine_l = 120
    
    if (x < 0):
        temp = engine_l
        engine_l = engine_r
        engine_r = temp

    print('X = %d, Y = %d, Left = %d, Right = %d' % (x, y, engine_l * engine_l_dir, engine_r * engine_r_dir))
    if (servo):
        engine_l = engine_l / 120 * engine_l_dir * 0.5 + 1.5
        engine_r = engine_r / 120 * engine_r_dir * 0.5 + 1.5
        setServoPulse(4, engine_l)
        setServoPulse(5, engine_r)
    else:
        if (velocity):
            if (engine_l_dir):
                if (engine_l_dir > 0):
                    # AIN1 L AIN2 H CCW
                    GPIO.output(12, GPIO.LOW)
                    GPIO.output(16, GPIO.HIGH)
                else:
                    # AIN1 H AIN2 L CW
                    GPIO.output(12, GPIO.HIGH)
                    GPIO.output(16, GPIO.LOW)
                pwma.ChangeDutyCycle(engine_l / 120 * 100)
            else:
                # AIN1 L AIN2 L STOP
                GPIO.output(12, GPIO.LOW)
                GPIO.output(16, GPIO.LOW)
            
            if (engine_r_dir):
                if (engine_r_dir > 0):
                    # BIN1 L BIN2 H CCW
                    GPIO.output(15, GPIO.LOW)
                    GPIO.output(13, GPIO.HIGH)
                else:
                    # BIN1 H BIN2 L CW
                    GPIO.output(15, GPIO.HIGH)
                    GPIO.output(13, GPIO.LOW)
                pwmb.ChangeDutyCycle(engine_r / 120 * 100)
            else:
                # BIN1 L BIN2 L STOP
                GPIO.output(15, GPIO.LOW)
                GPIO.output(13, GPIO.LOW)
            GPIO.output(7, GPIO.HIGH)
        else:
            GPIO.output(7, GPIO.LOW)