import os
import fcntl
import hexdump
import time
#import zlib

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
        self.hidraw = os.open('/dev/hidraw0', os.O_RDWR)
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
        if buf[0] != REPORT_ID:
            print('Report ID = %d' % (buf[0]))
            return
        x_raw = buf[3]
        y_raw = buf[4]
        non_move_guard = 7
        negative = 127 - non_move_guard
        positive = 128 + non_move_guard
        x = 0
        y = 0
        if (x_raw < negative):
            x = x_raw - negative
        elif (x_raw > positive):
            x = x_raw - positive
        if (y_raw < negative):
            y = negative - y_raw
        elif (y_raw > positive):
            y = positive - y_raw
        print('X = %d, Y = %d' % (x, y))
    def report_loop(self):
        while True:
            self.read()

ds4 = dualshock4()
ds4.report_loop()