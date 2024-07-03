import socket

from plico.utils.logger import Logger
from plico.utils.decorator import override
from plico.utils.reconnect import Reconnecting, reconnect
from plico_motor_server.devices.abstract_motor import AbstractMotor
from plico_motor.types.motor_status import MotorStatus


class PicomotorException(Exception):
    pass


class MyTcpSocket(socket.socket):
    '''
    TCP socket with verbose flag, for debug purposes
    '''

    def __init__(self, verbose=False):
        self._verbose = verbose
        super().__init__(socket.AF_INET, socket.SOCK_STREAM)

    def send(self, bytes, flags=0):
        if self._verbose:
            print('WRITING:', bytes)
        super().send(bytes, flags)

    def recv(self, bufsize, flags=0):
        if self._verbose:
            print('READING: ', end='')
        msg = super().recv(bufsize, flags)
        if self._verbose:
            print(msg)
        return msg


class Picomotor(AbstractMotor, Reconnecting):
    '''Picomotor class.
    '''

    def __init__(self,
                 ipaddr,
                 port=23,
                 naxis=4,
                 timeout=2,
                 name='Picomotor',
                 verbose=False,
                 **_):
        self._name = name
        self.ipaddr = ipaddr
        self.port = port
        self.timeout = timeout
        self.logger = Logger.of('Picomotor')
        self.naxis = naxis
        self.verbose = verbose
        self._logger = Logger.of("Picomotor")

        self._actual_position_in_steps = [0] * naxis
        self._has_been_homed = [False] * naxis
        self._last_commanded_position = [0] * naxis
        self._sock = None
        Reconnecting.__init__(self,
            self.connect,
            self.disconnect,
            [socket.timeout],
        )

    def connect(self):
        self._logger.notice('Connecting to picomotor at %s' % self.ipaddr)
        self._sock = MyTcpSocket(self.verbose)
        self._sock.settimeout(self.timeout)
        self._sock.connect((self.ipaddr, self.port))

    def disconnect(self):
        self._sock.close()

    @override
    def naxes(self):
        return self.naxis

    def _cmd(self, axis, cmd, *args):
        '''
        Send a command to the motor
        '''
        cmdstr = '%d%s' % (axis, cmd)
        cmdstr += ','.join(map(str, args)) + '\n'
        self._sock.send(cmdstr.encode())
        self._logger.debug('Sent command %r' % (cmdstr))

    def _ask(self, axis, cmd, *args):
        self._cmd(axis, cmd, *args)
        ans = self._sock.recv(128)

        # There are some garbage bytes when reconnecting, skip them
        if ans[0] == 255:
            ans = self._sock.recv(128)
        # According to newfocus8742 the reply must end with \r\n
        assert ans[-2:] == b'\r\n'
        return ans.strip()

    @reconnect
    def _moveby(self, axis, steps):
        self._logger.notice('Moving axis %d by %d steps' % (axis, steps))
        self._cmd(axis, 'PR', steps)

    @override
    def name(self):
        return self._name

    @override
    def home(self, axis):
        raise PicomotorException('Home command is not supported')

    @reconnect
    @override
    def position(self, axis):
        curr_pos = int(self._ask(axis, 'PA?'))
        self._logger.debug(
            'Current position axis %d = %d steps' % (axis, curr_pos))
        return curr_pos

    @override
    def move_to(self, axis, position_in_steps):
        delta = position_in_steps - self.position(axis)
        self._last_commanded_position[axis - 1] = position_in_steps
        return self._moveby(axis, delta)

    @override
    def velocity(self, axis):
        return 0

    @override
    def set_velocity(self, axis, velocity):
        raise PicomotorException('Set velocity command is not implemented')

    @override
    def stop(self, axis):
        raise PicomotorException('Stop command is not supported')

    @override
    def deinitialize(self, axis):
        raise PicomotorException('Deinitialize command is not supported')

    @override
    def steps_per_SI_unit(self, axis):
        return 1.0 / 20e-9  #  20 nanometers/step (TBC)

    @override
    def was_homed(self, axis):
        return True

    @override
    def type(self, axis):
        return MotorStatus.TYPE_LINEAR

    @override
    def is_moving(self, axis):
        return False  # TBD

    @override
    def last_commanded_position(self, axis):
        return self._last_commanded_position[axis - 1]
