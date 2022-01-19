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

GET_ID = "*idn? (CR)"
READ_WL = "pos? (CR)"
WRITE_WL = "pos=%5.3f (CR)"

class FilterWheelException(Exception):
    pass

class SerialTimeoutException(Exception):
    def __init__(self, value=-1):
        print ("Missing response from serial after %i iterrations" % value)

class FilterWheel(AbstractMotor):

    def __init__(self, name, port, speed):
        """The constructor """
        self._name = name
        self.port = port
        self.speed = speed
        self.naxis = 1
        self.ser = None
        self._logger = Logger.of("FilterWheel")
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
            self._logger.notice('Connecting to filter wheel at %s' % self.port)
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

    def get_id(self):
        cmd = bytes(GET_ID, 'utf-8')
        tmp = self.ser.write(cmd)
        nw = self._pollSerial()
        out = self.ser.read(self.ser.inWaiting())
        return out

    def _get_pos(self):
        '''
        Returns
        -------
        out: ?
        '''
        cmd = bytes(READ_WL, 'utf-8')
        tmp = self.ser.write(cmd)
        nw = self._pollSerial()
        out = self.ser.read(self.ser.inWaiting())
        return out

    def _set_pos(self, n):
        '''
        Parameters
        ----------
        n: int
            number of filter position selected

        Returns
        -------
        out: ?
        '''
        if wl < 650 or wl > 1100:
            raise BaseException()
        cmd = bytes(WRITE_WL % wl, 'utf-8')
        tmp = self.ser.write(cmd)
        nw = self._pollSerial()
        out = self.ser.read(self.ser.inWaiting())
        return out



### Per classe astratta ###

    @override
    def name(self):
        return self._name

    @override
    def position(self, axis):
        curr_pos = self._get_wl()
        self._logger.debug(
            'Current position = %d nm' % curr_pos)
        return curr_pos

    @override
    def steps_per_SI_unit(self, axis):
        raise FilterWheelException('One step is equal to one nanometer.')

    @override
    def was_homed(self, axis):
        raise FilterWheelException('Command not yet implemented.')

    @override
    def type(self, axis):
        return MotorStatus.TYPE_ROTARY

    @override
    def is_moving(self, axis):
        raise FilterWheelException('Command not yet implemented.')

    @override
    def last_commanded_position(self, axis):
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
        raise FilterWheelException('Home command is not supported.')
    
    @override
    def move_to(self, axis, number_of_filter_position):
        position = self._set_wl(number_of_filter_position)
        self._last_commanded_position.append(position)
        return

    @override
    def stop(self, axis):
        raise FilterWheelException('Stop command is not supported.')

    @override
    def deinitialize(self, axis):
        raise FilterWheelException('Deinitialize command is not supported.')
