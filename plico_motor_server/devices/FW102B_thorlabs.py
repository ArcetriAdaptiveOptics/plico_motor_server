'''
Authors
  - C. Selmi: written in 2022
  - Cascading bench: FW102C-compatible serial I/O (*idn? optional; wait for '>')
'''
import re
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
        print("Missing response from serial after %i iterrations" % value)


class FilterWheel(AbstractMotor, Reconnecting):
    '''
    Manual: https://www.thorlabs.com/drawings/67124bd78341d22e-A3AF90CF-D9E9-9FC4-63EEF4724CA5DD84/FW102C-Manual.pdf

    Some FW102C firmwares do not implement *idn? (CMD_NOT_DEFINED). Connect
    verifies the link with pos? and waits for the '>' prompt on every reply.
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
            [SerialTimeoutException, FilterWheelException],
        )

    def _flush_input(self):
        if self.ser is not None:
            time.sleep(0.05)
            try:
                self.ser.reset_input_buffer()
            except Exception:
                pass

    def _transact(self, cmd, timeout_s=2.0):
        '''Write cmd and read until FW prompt ">" or timeout.'''
        if self.ser is None:
            raise FilterWheelException('Serial port is not open')
        self._flush_input()
        self.ser.write(cmd.encode('utf-8') if isinstance(cmd, str) else cmd)
        buf = bytearray()
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            n = self.ser.inWaiting()
            if n:
                buf.extend(self.ser.read(n))
                if b'>' in buf:
                    time.sleep(0.02)
                    if self.ser.inWaiting():
                        buf.extend(self.ser.read(self.ser.inWaiting()))
                    return buf.decode('utf-8', errors='replace')
            time.sleep(0.01)
        raise SerialTimeoutException()

    @staticmethod
    def _parse_id(out_s):
        if 'CMD_NOT_DEFINED' in out_s or 'Command error' in out_s:
            return 'FW102'
        parts = [p.strip() for p in re.split(r'[\r\n]+', out_s) if p.strip()]
        for p in parts:
            if p.lower().startswith('*idn'):
                continue
            if p == '>' or p.lower().startswith('command error'):
                continue
            return p
        return 'FW102'

    @staticmethod
    def _parse_pos(out_s):
        # Typical: "pos?\r2\r> "  (echo + position + prompt)
        if 'CMD_NOT_DEFINED' in out_s or 'Command error' in out_s:
            raise FilterWheelException('Device error in reply: %r' % out_s)
        m = re.search(r'pos\?\s*[\r\n]+\s*(\d+)', out_s, flags=re.IGNORECASE)
        if m:
            return int(m.group(1))
        for tok in re.findall(r'\d+', out_s):
            n = int(tok)
            if 1 <= n <= 6:
                return n
        raise FilterWheelException('Could not parse position response: %r' % out_s)

    def _read_position_raw(self):
        return self._parse_pos(self._transact(READ_N))

    def connect(self):
        if self.ser is not None:
            return
        time.sleep(1)  # Slow down reconnect loops
        port = self.serial_or_usb.port_name()
        self._logger.notice('Connecting to filter wheel at %s' % port)
        self.ser = serial.Serial(port, self.speed,
                                 bytesize=serial.EIGHTBITS,
                                 parity=serial.PARITY_NONE,
                                 stopbits=serial.STOPBITS_ONE)
        time.sleep(0.2)
        # Use raw I/O here — do not call @reconnect methods from connect()
        pos = self._read_position_raw()
        self._logger.notice(
            'Filter wheel connected at %s, position=%d' % (port, pos))
        return pos

    def disconnect(self):
        if self.ser is not None:
            try:
                self.ser.close()
            except Exception:
                pass
            self.ser = None

    @reconnect
    def get_id(self):
        '''
        Returns
        ------
        out = string
            motor model type
        '''
        return self._parse_id(self._transact(GET_ID))

    @reconnect
    def _get_pos(self):
        '''
        Returns
        -------
        out: int
            number of filter wheel position
        '''
        return self._read_position_raw()

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
            confirmed filter wheel position
        '''
        if n < 1 or n > 6:
            raise FilterWheelException('Position %d is out of range (1-6)' % n)
        self._transact(WRITE_N % n)
        # Wheel motion can take ~1s; confirm final position
        time.sleep(1.0)
        return self._read_position_raw()


### Per classe astratta ###

    @override
    def name(self):
        return self._name

    @override
    def position(self, axis):
        curr_pos = self._get_pos()
        self._logger.debug('Current position = %d' % curr_pos)
        return curr_pos

    @override
    def velocity(self, axis):
        return 0.0

    @override
    def steps_per_SI_unit(self, axis):
        return 1

    @override
    def was_homed(self, axis):
        return True

    @override
    def type(self, axis):
        return MotorStatus.TYPE_ROTARY

    @override
    def is_moving(self, axis):
        return False

    @override
    def last_commanded_position(self, axis):
        return self._last_commanded_position

    @override
    def naxes(self):
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
