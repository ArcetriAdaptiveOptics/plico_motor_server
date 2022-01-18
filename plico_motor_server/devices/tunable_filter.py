'''
Authors
  - C. Selmi: written in 2021
'''
import os
import time
import yaml
import serial

WRITE_WL = "WL=%5.3f\r"
READ_WL = "WL?\r"
RESET = "R1\r"
READ_STATUS = "@"
BUSY_CHECK = "!"
ESCAPE = chr(27)

class SerialTimeoutException(Exception):
    def __init__(self, value=-1):
        print ("Missing response from serial after %i iterrations" % value)

class TunableFilter(AbstractMotor):

    def __init__(self, name, port, speed):
        """The constructor """
        self._name = name
        self.port = port
        self.speed = speed
        self.ser = None

    def _pollSerial(self):
        nw = 0
        nw0 = 0
        it = 0
        while True:
            nw = self.ser.inWaiting()
            it = it + 1
            time.sleep(0.01)
            if (nw >0) and (nw0==nw) or (it==10000):
                break
            nw0 = nw
        if nw == 0:
            raise SerialTimeoutException(it)
        else:
            return nw

    def connect(self):
        if self.ser is None:
            self.ser = serial.Serial(self.port, self.speed,
                                     bytesize=serial.EIGHTBITS,
                                     parity=serial.PARITY_NONE,
                                     stopbits=serial.STOPBITS_ONE)
            out = self.get_status()
            return out
        else:
            print ("Already connected")

    def disconnect(self):
        if self.ser is not None:
            self.ser.close()
            self.ser = None

    def _get_wl(self):
        '''
        Returns
        -------
        out: int [nm]
            wavelength output from filter
        '''
        cmd = bytes(READ_WL, 'utf-8')
        tmp = self.ser.write(cmd)
        nw = self._pollSerial()
        out = self.ser.read(self.ser.inWaiting())
        return out

    def _set_wl(self, wl):
        '''
        Parameters
        ----------
        wl: int [nm]
            wavelength to set

        Returns
        -------
        out: int [nm]
            wavelength output from filter
        '''
        if wl < 650 or wl > 1100:
            raise BaseException()
        cmd = bytes(WRITE_WL % wl, 'utf-8')
        tmp = self.ser.write(cmd)
        nw = self._pollSerial()
        out = self.ser.read(self.ser.inWaiting())
        return out

    def reset(self):
        '''
        Returns
        -------
        out:
        '''
        cmd = bytes(RESET, 'utf-8')
        tmp = self.ser.write(cmd)
        nw = self._pollSerial()
        out = self.ser.read(self.ser.inWaiting())
        return out

    def get_status(self):
        '''
        Returns
        -------
        out:
        '''
        cmd = bytes(READ_STATUS, 'utf-8')
        tmp = self.ser.write(cmd)
        nw = self._pollSerial()
        out = self.ser.read(self.ser.inWaiting())
        return out

    def isbusy(self):
        '''
        Returns
        -------
        out:
        '''
        cmd = bytes(BUSY_CHECK, 'utf-8')
        tmp = self.ser.write(cmd)
        nw = self._pollSerial()
        out = self.ser.read(self.ser.inWaiting())
        return out

    def cancel(self):
        '''
        Returns
        -------
        out:
        '''
        cmd = bytes(ESCAPE, 'utf-8')
        tmp = self.ser.write(cmd)
        nw = self._pollSerial()
        out = self.ser.read(self.ser.inWaiting())
        return out

    @override
    def name(self):
        return self._name

    @override
    def position(self, axis):
        curr_pos = self._get_wl()
        self._logger.debug(
            'Current position axis %d = %d nm' % (axis, curr_pos))
        return curr_pos

    @override
    def move_to(self, axis, absolute_position_in_nm):
        absolute_position_in_nm = self._set_wl(absolute_position_in_nm)
        return 

    @override
    def home(self, axis):
        pass
        #raise Exception('Home command is not supported')