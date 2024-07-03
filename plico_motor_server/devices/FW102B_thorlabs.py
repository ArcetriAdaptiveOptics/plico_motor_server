'''
Authors
  - C. Selmi: written in 2022
'''
import time
import serial
from plico.utils.logger import Logger
from plico.utils.decorator import override
from plico.utils.reconnect import Reconnecting, reconnect
from plico_motor_server.devices.abstract_motor import AbstractMotor
from plico_motor.types.motor_status import MotorStatus


GET_ID = "*idn?\r"
READ_N = "pos?\r"
WRITE_N = "pos=%d\r"


class FilterWheelException(Exception):
    pass


class SerialTimeoutException(Exception):
    def __init__(self, value=-1):
        print ("Missing response from serial after %i iterrations" % value)


class FilterWheel(AbstractMotor, Reconnecting):
    '''
    Manual: https://www.thorlabs.com/drawings/67124bd78341d22e-A3AF90CF-D9E9-9FC4-63EEF4724CA5DD84/FW102C-Manual.pdf
    '''
    def __init__(self, name, serial_or_usb, speed):
        """The constructor """
        self._name = name
        self.serial_or_usb = serial_or_usb
        self.speed = speed
        self.naxis = 1
        self.ser = None
        self._logger = Logger.of("FilterWheel")
        self._last_commanded_position = None
        Reconnecting.__init__(self,
            self.connect,
            self.disconnect,
            [SerialTimeoutException],
        )

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
            time.sleep(1) # Slow down reconnect loops
            port = self.serial_or_usb.port_name()
            self._logger.notice('Connecting to filter wheel at %s' % port)
            self.ser = serial.Serial(port, self.speed,
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

    @reconnect
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

    @reconnect
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

    @reconnect
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
            raise FilterWheelException('Position %d is out of range (1-6)' % n)
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
        curr_pos: int
            output number position from filter
        '''
        curr_pos = self._get_pos()
        self._logger.debug(
            'Current position = %d nm' % curr_pos)
        return curr_pos

    @override
    def velocity(self, axis):
        '''
        Returns
        -------
        velocity: float
            Motor velocity. Since this is not supported, it is always zero.
        '''
        return 0.0

    @override
    def steps_per_SI_unit(self, axis):
        return 1

    @override
    def was_homed(self, axis):
        return True

    @override
    def type(self, axis):
        '''
        Returns
        -------
        type: string
             type of motor controller
        '''
        return MotorStatus.TYPE_ROTARY

    @override
    def is_moving(self, axis):
        return False

    @override
    def last_commanded_position(self, axis):
        '''
        Returns
        ------
        last commanded position: int
            last number commanded position
        '''
        return self._last_commanded_position

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
        position = self._set_pos(number_of_filter_position)
        self._last_commanded_position = position
        return

    @override
    def stop(self, axis):
        raise FilterWheelException('Stop command is not supported.')

    @override
    def deinitialize(self, axis):
        raise FilterWheelException('Deinitialize command is not supported.')

    @override
    def set_velocity(self, velocity, axis):
        raise FilterWheelException('Set_velocity command is not supported.')
