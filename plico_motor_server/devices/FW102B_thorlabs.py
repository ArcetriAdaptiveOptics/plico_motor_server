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

GET_ID = "*idn?\r"
READ_N = "pos?\r"
WRITE_N = "pos=%d\r"

class FilterWheelException(Exception):
    pass

class SerialTimeoutException(Exception):
    def __init__(self, value=-1):
        print ("Missing response from serial after %i iterrations" % value)

class FilterWheel(AbstractMotor):
    '''
    Manual: https://www.thorlabs.com/drawings/67124bd78341d22e-A3AF90CF-D9E9-9FC4-63EEF4724CA5DD84/FW102C-Manual.pdf
    '''

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
            out = self.get_id()
            return out
        else:
            print ("Already connected")

    def disconnect(self):
        if self.ser is not None:
            self.ser.close()
            self.ser = None

    def get_id(self):
        '''
        Returns
        ------
        out = string
            motor model type
        '''
        cmd = bytes(GET_ID, 'utf-8')
        tmp = self.ser.write(cmd)
        nw = self._pollSerial()
        out_b = self.ser.read(self.ser.inWaiting())
        out_s = out_b.decode('utf-8')
        out = out_s.split('\r')[1]
        return out

    def _get_pos(self):
        '''
        Returns
        -------
        out: int
            number of filter wheel position
        '''
        cmd = bytes(READ_N, 'utf-8')
        tmp = self.ser.write(cmd)
        nw = self._pollSerial()
        out_b = self.ser.read(self.ser.inWaiting())
        out_s = out_b.decode('utf-8')
        out = int(out_s.split()[1])
        return out

    def _set_pos(self, n):
        '''
        Parameters
        ----------
        n: int
            number of filter position selected

        Returns
        -------
        out: int
            number of filter wheel position
        '''
        if n < 1 or n > 6:
            raise BaseException()
        cmd = bytes(WRITE_N % n, 'utf-8')
        tmp = self.ser.write(cmd)
        nw = self._pollSerial()
        out_b = self.ser.read(self.ser.inWaiting())
        out_s = out_b.decode('utf-8')
        out = out_s.split()[0]
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
        raise FilterWheelException('One step is equal to one filter position.')

    @override
    def was_homed(self, axis):
        raise FilterWheelException('Home command is not supported.')

    @override
    def type(self, axis):
        return MotorStatus.TYPE_ROTARY

    @override
    def is_moving(self, axis):
        raise FilterWheelException('Moving command is not supported.')

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
