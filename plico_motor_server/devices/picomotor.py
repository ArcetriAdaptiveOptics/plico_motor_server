import socket

from plico.utils.logger import Logger
from plico.utils.decorator import override
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


def _reconnect(f):
    '''
    Make sure that the function is executed
    after connecting to the motor, and trigger
    a reconnect in the next command if any error occurs.

    Any communication problem will raise a PicomotorException
    '''

    def func(self, *args, **kwargs):
        try:
            if not self._sock:
                self._connect()
            return f(self, *args, **kwargs)
        except socket.timeout:
            self._sock = None
            raise PicomotorException

    return func


class Picomotor(AbstractMotor):
    '''Picomotor class.
    '''

    def __init__(self,
                 ipaddr,
                 port=23,
                 axis=1,
                 timeout=2,
                 name='Picomotor',
                 verbose=False,
                 **_):
        self._name = name
        self.ipaddr = ipaddr
        self.port = port
        self.timeout = timeout
        self.logger = Logger.of('Picomotor')
        self.axis = axis
        self.verbose = verbose

        self._actual_position_in_steps = 0
        self._has_been_homed = False
        self._last_commanded_position = 0
        self._sock = None

    def _connect(self):
        if self.verbose:
            print('Connecting to picomotor at', self.ipaddr)
        self._sock = MyTcpSocket(self.verbose)
        self._sock.settimeout(self.timeout)
        self._sock.connect((self.ipaddr, self.port))

    def _cmd(self, cmd, *args):
        '''
        Send a command to the motor
        '''
        cmdstr = '%d%s' % (self.axis, cmd)
        cmdstr += ','.join(map(str, args)) + '\n'
        self._sock.send(cmdstr.encode())

    def _ask(self, cmd, *args):
        self._cmd(cmd, *args)
        ans = self._sock.recv(128)

        # There are some garbage bytes when reconnecting, skip them
        if ans[0] == 255:
            ans = self._sock.recv(128)
        return ans.strip()

    @_reconnect
    def _moveby(self, steps):
        if self.verbose:
            print('Moving by %d steps' % steps)
        self._cmd('PR', steps)

    @override
    def name(self):
        return self._name

    @override
    def home(self):
        raise PicomotorException('Home command is not supported')

    @_reconnect
    @override
    def position(self):
        return int(self._ask('PA?'))

    @override
    def move_to(self, position_in_steps):
        delta = position_in_steps - self.position()
        self._last_commanded_position = position_in_steps
        return self._moveby(delta)

    @override
    def stop(self):
        raise PicomotorException('Stop command is not supported')

    @override
    def deinitialize(self):
        raise PicomotorException('Deinitialize command is not supported')

    @override
    def steps_per_SI_unit(self):
        return 1.0 / 20e-9  #  20 nanometers/step (TBC)

    @override
    def was_homed(self):
        return True

    @override
    def type(self):
        return MotorStatus.TYPE_LINEAR

    @override
    def is_moving(self):
        return False  # TBD

    @override
    def last_commanded_position(self):
        return self._last_commanded_position
