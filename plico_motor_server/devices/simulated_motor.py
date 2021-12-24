from plico.utils.decorator import override
from plico.utils.logger import Logger
from plico_motor_server.devices.abstract_motor import AbstractMotor
from plico_motor.types.motor_status import MotorStatus


class SimulatedMotor(AbstractMotor):
    STEP_PER_M = 123456789
    MAX_VALUE = 65000

    def __init__(self, name='Simulated Motor'):
        self._name = name
        self._logger = Logger.of('SimulatedMotor')
        self._actual_position_in_steps = 657
        self._position_in_steps = 0
        self._noise_in_steps = 0
        self._has_been_homed = False
        self._is_moving = False
        self._raiseExceptionOnDeinitialize = False

    @override
    def name(self):
        return self._name

    @override
    def home(self):
        self._logger.notice('Simulated motor initialized')
        self._actual_position_in_steps = 0
        self._position_in_steps = 0
        self._has_been_homed = True

    @override
    def position(self):
        return self._position_in_steps

    @override
    def move_to(self, position_in_steps):
        self._position_in_steps = position_in_steps

    @override
    def stop(self):
        self._is_moving = False

    def raise_exception_on_deinitialize(self, trueOrFalse):
        self._raiseExceptionOnDeinitialize = trueOrFalse

    @override
    def deinitialize(self):
        if self._raiseExceptionOnDeinitialize:
            raise Exception('Asked to fail on deinitialize')
        else:
            pass

    @override
    def steps_per_SI_unit(self):
        return 1

    @override
    def was_homed(self):
        return self._has_been_homed

    @override
    def type(self):
        return MotorStatus.TYPE_LINEAR

    @override
    def is_moving(self):
        return False

    @override
    def last_commanded_position(self):
        return self._position_in_steps

