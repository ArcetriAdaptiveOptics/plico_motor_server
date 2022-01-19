'''
Authors
  - C. Selmi: written in 2022
'''
import os
import time
import serial
from plico.utils.logger import Logger
from plico.utils.decorator import override
from plico_motor_server.devices.abstract_motor import AbstractMotor

WRITE_WL = "WL=%5.3f\r"
READ_WL = "WL?\r"
RESET = "R1\r"
READ_STATUS = "@"
BUSY_CHECK = "!"
ESCAPE = chr(27)

class TunableFilterException(Exception):
    pass

class SerialTimeoutException(Exception):
    def __init__(self, value=-1):
        print ("Missing response from serial after %i iterrations" % value)

class TunableFilter(AbstractMotor):

    def __init__(self, name, port, speed):
        """The constructor """
        self._name = name
        self.port = port
        self.speed = speed
        self.naxis = 1
        self.ser = None
        self._logger = Logger.of("TunableFilter")
        self._last_commanded_position = []

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
            self._logger.notice('Connecting to tunable filter at %s' % self.port)
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

    def _reset(self):
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

    def _get_status(self):
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

    def _isbusy(self):
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

    def _cancel(self):
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

### Per classe astratta ###

    @override
    def name(self):
        '''
        Returns
        -------
        name: string
            filter name
        '''
        return self._name

    @override
    def position(self, axis):
        '''
        Returns
        -------
        curr_pos: int [nm]
            wavelength output from filter
        '''
        curr_pos = self._get_wl()
        self._logger.debug(
            'Current position = %d nm' % curr_pos)
        return curr_pos

    @override
    def steps_per_SI_unit(self, axis):
        raise TunableFilterException('One step is equal to one nanometer.')
    
    @override
    def was_homed(self, axis):
        raise TunableFilterException('Command not yet implemented.')
    
    @override
    def type(self, axis):
        '''
        Returns
        -------
        type: string
             type of motor controller
        '''
        return MotorStatus.TYPE_LINEAR
    
    @override
    def is_moving(self, axis):
        out = self._isbusy()
        return out

    @override
    def last_commanded_position(self, axis):
        '''
        Returns
        ------
        last commanded position: int
            last set point in nm contained in last commanded position list
        '''
        return self._last_commanded_position[-1]

    @override
    def naxes(self):
        '''
        Returns
        ------
        naxes: int
            number of motor axes
        '''
        return self.naxis
    
    @override
    def home(self, axis):
        raise TunableFilterException('Home command is not supported.')
    
    @override
    def move_to(self, axis, absolute_position_in_nm):
        '''
        Move to an absolute position

        Parameters
        ----------
        position: int [nm]
            desired lambda position in nanometres
        '''
        absolute_position_in_nm = self._set_wl(absolute_position_in_nm)
        self._last_commanded_position.append(absolute_position_in_nm)
        return

    @override
    def stop(self, axis):
        out = self._cancel()
        return out

    @override
    def deinitialize(self, axis):
        raise TunableFilterException('Deinitialize command is not supported.')

    