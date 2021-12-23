import asyncio
from newfocus8742 import tcp

from plico.utils.logger import Logger
from plico.utils.decorator import override
from plico_motor_server.devices.abstract_motor import AbstractMotor
from plico_motor.types import MotorStatus



class PicomotorException(Exception):
    pass


def _reconnect(f):
    '''
    Make sure that the function is executed
    after connecting to the motor, and trigger
    a reconnect in the next command if any error occurs.

    Any communication problem will raise a PicomotorException
    '''
    async def func(self, *args, **kwargs):
        try:
            if not self.connected:
                await self._connect()
            return await f(self, *args, **kwargs)
        except (asyncio.TimeoutError, OSError):
            self.connected = False
            raise PicomotorException
    return func


class PicoMotor(AbstractMotor):
    '''Picomotor class.
       Hides the asyncio event loop, exposing synchronous methods
    '''

    def __init__(self, ipaddr, axis=1, timeout=2, name='Picomotor', verbose=False):
        self.name = name
        self.ipaddr = ipaddr
        self.timeout = timeout
        self.logger = Logger.of('Picomotor')
        self.is_moving = False
        self._actual_position_in_steps = 0
        self._has_been_homed = False
        self.loop = asyncio.get_event_loop()
        self.verbose = verbose
        self._last_commanded_position = 0

    async def _connect(self):
        if self.verbose:
            print('Connecting to picomotor at', self.ipaddr)
        future = tcp.NewFocus8742TCP.connect(self.ipaddr)
        self.motor = await asyncio.wait_for(future, self.timeout)
        self.connected = True

    async def _timeout(self, future):
        '''Wrapper for awaitable futures, adding a timeout'''
        return await asyncio.wait_for(future, self.timeout)

    @_reconnect
    async def _moveby(self, steps, block=True):

        if self.verbose:
            print('Moving by %d steps', steps)

        self.motor.set_relative(self.axis, steps)
        if block:
            if self.verbose:
                print('Waiting for completion')
            while await self._timeout(self.motor.done(self.axis)):
                await asyncio.sleep(self.poll_interval)

    @_reconnect
    async def _pos(self):
        return await self._timeout(self.motor.position(self.axis))

    @override
    def name(self):
        return self._name

    @override
    def home(self):
        raise PicomotorException('Home command is not supported')

    @override
    def position(self):
        return self.loop.run_until_complete(self._pos())

    @override
    def move_to(self, position_in_steps, block=True):
        delta = position_in_steps - self.position()
        self._last_commanded_position = position_in_steps,
        return self.loop.run_until_complete(self._moveby(delta, block))

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
        return False   # TBD

    @override
    def last_commanded_position(self):
        return self._last_commanded_position
