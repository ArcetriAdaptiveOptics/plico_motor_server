'''
Authors
  - A. Puglisi: written in 2022
'''
from plico.utils.logger import Logger
from plico.utils.decorator import override
from plico_motor_server.devices.abstract_motor import AbstractMotor
from plico_motor.types.motor_status import MotorStatus


class GCSException(Exception):
    pass

def _reconnect(f):
    '''
    Make sure that the function is executed
    after connecting to the motor, and trigger
    a reconnect in the next command if any error occurs.

    Any communication problem will raise a FilterWheelException
    '''
    def func(self, *args, **kwargs):
        try:
            if not self.gcs:
                self.connect()
            return f(self, *args, **kwargs)
        except OSError:
            self.disconnect()
            raise FilterWheelFatalException('Error communicating with filter wheel. Will retry...')
        except FilterWheelException:
            raise

    return func

 
class PIGCS_Motor(AbstractMotor):
    '''
    Motor using the PI GCS communication protocol with a serial or USB connection.
    Makes use of the pipython module: https://github.com/PI-PhysikInstrumente/PIPython
    pipython is imported lazily and does not need to be installed until
    an instance of this class is initialized.
    '''

    def __init__(self, name, port, speed):
        from pipython import GCSDevice # Not used here, but let's fail now instead of later
        self._name = name
        self.port = port
        self.speed = speed
        self.naxis = 1
        self.gcs = None
        self._logger = Logger.of('GCS')
        self._last_commanded_position = None

    def connect(self):
        if self.gcs is None:
            from pipython import GCSDevice
            self._logger.notice('Connecting to GCS device at %s' % self.port)
            self.gcs = GCSDevice()
            self.gcs.ConnectRS232(self.port, self.speed)
        else:
            print ("Already connected")

    def disconnect(self):
        if self.gcs is not None:
            self.gcs.close()
            self.gcs = None

    @override
    def naxes(self):
        return self.naxis

    @override
    def name(self):
        return self._name

    @override
    def home(self, axis):
        self.gcs.FRF(axis)

    @_reconnect
    @override
    def position(self, axis):
        posdict = self.gcs.qPOS(axis)
        return posdict(axis)

    @override
    def move_to(self, axis, position_in_steps):
        self.gcs.MOV(axis, position_in_steps)

    @override
    def stop(self, axis):
        raise GCSException('Stop command is not supported')

    @override
    def deinitialize(self, axis):
        raise GCSException('Deinitialize command is not supported')

    @override
    def steps_per_SI_unit(self, axis):
        return 1000    # Unit is mm

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

