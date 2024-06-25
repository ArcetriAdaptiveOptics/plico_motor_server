'''
Authors
  - C. Selmi: written in 2022
'''
import os
import time
import serial
from plico.utils.logger import Logger
from plico.utils.decorator import override
from plico.utils.reconnect import Reconnecting, reconnect
from plico_motor_server.devices.abstract_motor import AbstractMotor
from plico_motor.types.motor_status import MotorStatus

GET_ID = "*idn?\r"
WRITE_WL = "WL=%5.3f\r"
READ_WL = "WL?\r"
GET_STATUS = "ST?\r"
GET_TEMPERATURE = 'TP?\r'


class TunableFilterException(Exception):
    pass


class SerialTimeoutException(Exception):
    def __init__(self, value=-1):
        print ("Missing response from serial after %i iterrations" % value)


class TunableFilter(AbstractMotor, Reconnecting):
    '''
    Manual: https://www.thorlabs.com/drawings/67124bd78341d22e-A3AF90CF-D9E9-9FC4-63EEF4724CA5DD84/KURIOS-VB1-Manual.pdf
    '''

    def __init__(self, name, serial_or_usb, speed):
        """The constructor """
        self._name = name
        self.serial_or_usb = serial_or_usb
        self.speed = speed
        self.naxis = 1
        self.ser = None
        self._logger = Logger.of("TunableFilter")
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
            self._logger.notice('Connecting to tunable filter at %s' % port)
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
        out = out_s.split('\r')[0]
        return out

    @reconnect
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
        out_b = self.ser.read(self.ser.inWaiting())
        out_s = out_b.decode('utf-8')
        out = out_s.split('\r')[0]
        out_number = float(out.split('=')[1])
        return out_number

    @reconnect
    def _set_wl(self, wl):
        '''
        Parameters
        ----------
        wl: int [nm]
            wavelength to set

        Returns
        -------
        out: str [nm]
            wavelength output from filter
        '''
        if wl < 420 or wl > 730:
            raise TunableFilterException('Wavelength out of range 420-730')
        cmd = bytes(WRITE_WL % wl, 'utf-8')
        tmp = self.ser.write(cmd)
        nw = self._pollSerial()
        out_b = self.ser.read(self.ser.inWaiting())
        out_s = out_b.decode('utf-8')
        #out = out_s.split('\r')[0]
        #out = self._get_wl()
        return out_s

    @reconnect
    def _get_status(self):
        '''
        Returns
        -------
        out: byte
            Returns current filter status:
            0 - initialization
            1 - warm up
            2 - ready
        '''
        cmd = bytes(GET_STATUS, 'utf-8')
        tmp = self.ser.write(cmd)
        nw = self._pollSerial()
        out_b = self.ser.read(self.ser.inWaiting())
        out_s = out_b.decode('utf-8')
        out = out_s.split()[0]
        return out
    
    @reconnect
    def get_temperature(self):
        '''
        Returns
        -------
        out: byte
            temperature
        '''
        cmd = bytes(GET_TEMPERATURE, 'utf-8')
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
        curr_pos: string [nm]
            wavelength output from filter
        '''
        curr_pos = self._get_wl()
        self._logger.debug(
            'Current position = %s nm' % curr_pos)
        return curr_pos

    @override
    def velocity(self, axis):
        '''
        Returns
        -------
        velocity: float
            Motor velocity. Always zero.
        '''
        return 0

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
        return MotorStatus.TYPE_LINEAR
    
    @override
    def is_moving(self, axis):
        return False

    @override
    def last_commanded_position(self, axis):
        '''
        Returns
        ------
        last commanded position: int
            last commanded position in nm
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
        self._last_commanded_position = absolute_position_in_nm
        return

    @override
    def stop(self, axis):
        raise TunableFilterException('Stop command is not supported.')

    @override
    def deinitialize(self, axis):
        raise TunableFilterException('Deinitialize command is not supported.')

    @override
    def set_velocity(self, axis):
        raise TunableFilterException('Set velocity command is not supported.')

    
