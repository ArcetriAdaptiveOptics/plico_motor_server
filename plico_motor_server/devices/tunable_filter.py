'''
Authors
  - C. Selmi: written in 2021
  - A. Puglisi: ported to plico_motor
'''
import yaml
import serial
import time

from plico.utils.logger import Logger
from plico.utils.decorator import override
from plico_motor_server.devices.abstract_motor import AbstractMotor
from plico_motor.types.motor_status import MotorStatus


class SerialTimeoutException(Exception):
    def __init__(self, value=-1):
        print ("Missing response from serial after %i iterrations" % value)


def _reconnect(f):
    '''
    Make sure that the function is executed
    after connecting to the motor, and trigger
    a reconnect in the next command if any error occurs.

    Any communication problem will raise a PicomotorException
    '''

    def func(self, *args, **kwargs):
        try:
            if not self.ser:
                self.connect()
            return f(self, *args, **kwargs)
        except SerialTimeoutException:
            self.ser = None
            raise

    return func


class TunableFilter(AbstractMotor):

    def __init__(self,
                 yamlFile,
                 name='TunableFilter',
                 verbose=False,
                 ):
        self._name = name
        self.currfilt = CurrentFilterReader(yamlFile)
        self.naxis = 1
        self.verbose = verbose
        self._logger = Logger.of("TunableFilter")

        self._actual_position_in_steps = 0
        self._has_been_homed = True  # Tunable filter position is absolute
        self._last_commanded_position = 0

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
            self.ser = serial.Serial(self.currfilt.port, self.currfilt.speed,
                                     bytesize=self.currfilt.data_bits,
                                     parity=self.currfilt.parity,
                                     stopbits=self.currfilt.stop_bits)
            out = self.get_status()
            return out

    @override
    def naxes(self):
        return 1

    @override
    def name(self):
        return self._name

    @override
    def home(self, axis):
        '''Tunable filter position is absolute, no need for homing'''
        pass

    @override
    def position(self, axis):
        assert axis == 1
        pos = self.get_wl().split()[2]
        self._logger.debug('Current tunable filter position = %d nm' % pos)
        return pos

    @override
    def move_to(self, axis, position_in_steps):
        assert axis == 1
        self.set_wl(position_in_steps)

    @override
    def stop(self, axis):
        '''Tunable filter is always "stopped"'''
        pass

    @override
    def deinitialize(self, axis):
        '''Tunable filter is absolute, no need for homing'''
        pass

    @override
    def steps_per_SI_unit(self, axis):
        return 1e9  # 1 step = 1nm

    @override
    def was_homed(self, axis):
        return True

    @override
    def type(self, axis):
        assert axis == 1
        return MotorStatus.TYPE_LINEAR

    @override
    def is_moving(self, axis):
        return False  # TBD

    @override
    def last_commanded_position(self, axis):
        assert axis == 1
        return self._last_commanded_position


    @_reconnect
    def get_wl(self):
        cmd = bytes(self.currfilt.read_wl, 'utf-8')
        tmp = self.ser.write(cmd)
        nw = self._pollSerial()
        out = self.ser.read(self.ser.inWaiting()) 
        return out

    @_reconnect
    def set_wl(self, wl):
        if wl < 420 or wl > 730:
            raise BaseException()
        cmd = bytes(self.currfilt.write_wl % wl, 'utf-8')
        tmp = self.ser.write(cmd)
        nw = self._pollSerial()
        out = self.ser.read(self.ser.inWaiting()) 
        return out

    @_reconnect
    def reset(self):
        cmd = bytes(self.currfilt.reset, 'utf-8')
        tmp = self.ser.write(cmd)
        nw = self._pollSerial()
        out = self.ser.read(self.ser.inWaiting()) 
        return out

    @_reconnect
    def get_status(self):
        cmd = bytes(self.currfilt.read_status, 'utf-8')
        tmp = self.ser.write(cmd)
        nw = self._pollSerial()
        out = self.ser.read(self.ser.inWaiting()) 
        return out

    @_reconnect
    def isbusy(self):
        cmd = bytes(self.currfilt.busy_check, 'utf-8')
        tmp = self.ser.write(cmd)
        nw = self._pollSerial()
        out = self.ser.read(self.ser.inWaiting()) 
        return out

    @_reconnect
    def cancel(self):
        cmd = bytes(self.currfilt.escape, 'utf-8')
        tmp = self.ser.write(cmd)
        nw = self._pollSerial()
        out = self.ser.read(self.ser.inWaiting()) 
        return out


class CurrentFilterReader():
    ''' class for reading data from yaml file
    '''

    def __init__(self, yamlFile):
        with open(yamlFile) as file:
            self._currFilt = yaml.load(file, Loader=yaml.FullLoader)

    @property
    def write_wl(self):
        return self._currFilt['WRITE_WL']

    @property
    def read_wl(self):
        return self._currFilt['READ_WL']

    @property
    def reset(self):
        return self._currFilt['RESET']

    @property
    def read_status(self):
        return self._currFilt['READ_STATUS']

    @property
    def busy_check(self):
        return self._currFilt['BUSY_CHECK']

    @property
    def escape(self):
        return self._currFilt['ESCAPE']

    @property
    def port(self):
        return self._currFilt['PORT']

    @property
    def baud_rate(self):
        return self._currFilt['SPEED']

    @property
    def data_bits(self):
        return self._currFilt['DATABITS']

    @property
    def parity(self):
        return self._currFilt['PARITY']

    @property
    def stop_bits(self):
        return self._currFilt['STOPBITS']

    @property
    def flow_controll(self):
        return self._currFilt['FLOWCONTROLL']


