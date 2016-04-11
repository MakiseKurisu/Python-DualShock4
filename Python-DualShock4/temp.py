#!/usr/bin/python

from Adafruit_PWM_Servo_Driver import PWM
import time
import signal
import sys

# ===========================================================================
# Example Code
# ===========================================================================

# Initialise the PWM device using the default address
pwm = PWM(0x40)
# Note if you'd like more debug output you can instead run:
#pwm = PWM(0x40, debug=True)

servoMin = 150  # Min pulse length out of 4096
servoMax = 600  # Max pulse length out of 4096

def setServoPulse(channel, pulse):
  pulseLength = 1000000                   # 1,000,000 us per second
  pulseLength /= 60                       # 60 Hz
  print "%d us per period" % pulseLength
  pulseLength /= 4096                     # 12 bits of resolution
  print "%d us per bit" % pulseLength
  pulse *= 1000
  pulse /= pulseLength
  pwm.setPWM(channel, 0, pulse)

def int_handler(signal, frame):
  pwm = PWM(0x40)
  pwm.setAllPWM(0, 0)
  sys.exit(0)

signal.signal(signal.SIGINT, int_handler)

pwm.setPWMFreq(60)                        # Set frequency to 60 Hz
#while (True):
  # Change speed of continuous servo on channel O
  #pwm.setAllPWM(0, servoMin)
  #time.sleep(1)
  #pwm.setAllPWM(0, servoMax)
  #time.sleep(1)

import os
import fcntl
import math
#import ptvsd

#ptvsd.enable_attach('test')
print('Waiting for debugger')
#ptvsd.wait_for_attach()
print('Attached')
#ptvsd.break_into_debugger()

_IOC_WRITE = 1
_IOC_READ = 2

_IOC_NRSHIFT = 0
_IOC_NRBITS = 8

_IOC_TYPESHIFT = _IOC_NRSHIFT + _IOC_NRBITS
_IOC_TYPEBITS = 8

_IOC_SIZESHIFT = _IOC_TYPESHIFT + _IOC_TYPEBITS
_IOC_SIZEBITS = 14

_IOC_DIRSHIFT = _IOC_SIZESHIFT + _IOC_SIZEBITS
_IOC_DIRBITS = 2

_IOC = lambda dir, type, nr, size: (((dir)  << _IOC_DIRSHIFT) | ((type) << _IOC_TYPESHIFT) | ((nr)   << _IOC_NRSHIFT) | ((size) << _IOC_SIZESHIFT))

HIDIOCSFEATURE = lambda len: _IOC(_IOC_WRITE | _IOC_READ, ord('H'), 0x06, len)
HIDIOCGFEATURE = lambda len: _IOC(_IOC_WRITE | _IOC_READ, ord('H'), 0x07, len)

GET_FEATURE_02_ID = 0x02
GET_FEATURE_02_SIZE = 37

REPORT_ID = 0x11
REPORT_SIZE = 78

class dualshock4(object):
    #def __init__(self, device):
    def __init__(self):
        self.hidraw = os.open('/dev/hidraw2', os.O_RDWR)
        ioc = HIDIOCGFEATURE(GET_FEATURE_02_SIZE)
        buf = bytearray(GET_FEATURE_02_SIZE)
        buf[0] = GET_FEATURE_02_ID
        fcntl.ioctl(self.hidraw, ioc, bytes(buf))
    def write(self, red, green, blue):
        buf = bytearray(REPORT_SIZE)
        buf[0] = REPORT_ID
        buf[3] = 0xf3
        buf[6] = 127
        buf[7] = 127
        buf[8] = 255
        buf[9] = 255
        buf[10] = 255
        buf[REPORT_SIZE - 1] = 0x30
        buf[REPORT_SIZE - 2] = 0x2c
        buf[REPORT_SIZE - 3] = 0xb8
        buf[REPORT_SIZE - 4] = 0xbc
        os.write(self.hidraw,buf)
    def read(self):
        buf = os.read(self.hidraw,REPORT_SIZE)
        axis = [0] * 2
        if buf[0] != REPORT_ID:
            #print('Report ID = %d' % (buf[0]))
            return axis
        x_raw = buf[3]
        y_raw = buf[4]
        non_move_guard = 7
        negative = 127 - non_move_guard
        positive = 128 + non_move_guard
        if (x_raw < negative):
            axis[0] = x_raw - negative
        elif (x_raw > positive):
            axis[0] = x_raw - positive
        if (y_raw < negative):
            axis[1] = negative - y_raw
        elif (y_raw > positive):
            axis[1] = positive - y_raw
        return axis
    def report_loop(self):
        while True:
            axis = self.read()
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
            pwm.setPWM(4, 0, int(engine_l))
            pwm.setPWM(5, 0, int(engine_r))
            print('X = %d, Y = %d, Left = %d, Right = %d' % (x, y, engine_l, engine_r))

ds4 = dualshock4()
ds4.report_loop()
