import abc
from six import with_metaclass


class AbstractMotor(with_metaclass(abc.ABCMeta, object)):

    # -------------
    # Queries

    @abc.abstractmethod
    def name(self):
        assert False

    @abc.abstractmethod
    def position(self, axis=1):
        '''
        Returns
        ------
        position: int
            axis position in steps
        '''
        assert False

    @abc.abstractmethod
    def velocity(self, axis=1):
        '''
        Returns
        ------
        velocity: float
            velocity in steps per second
        '''
        assert False

    @abc.abstractmethod
    def steps_per_SI_unit(self, axis=1):
        '''
        Returns
        ------
        steps_per_SI_unit: float
            steps/m if linear motor or steps/rad if rotative motor
        '''
        assert False

    @abc.abstractmethod
    def was_homed(self, axis=1):
        assert False

    @abc.abstractmethod
    def type(self, axis=1):
        assert False

    @abc.abstractmethod
    def is_moving(self, axis=1):
        assert False

    @abc.abstractmethod
    def last_commanded_position(self, axis=1):
        '''
        Returns
        ------
        last commanded position: int
            last set point in steps
        '''
        assert False

    @abc.abstractmethod
    def naxes(self):
        '''
        Returns
        ------
        naxes: int
            number of motor axes
        '''
        assert False

    # --------------
    # Commands

    @abc.abstractmethod
    def home(self, axis=1):
        '''
        Perform homing / initialization procedure
        '''
        assert False

    @abc.abstractmethod
    def move_to(self, axis=1):
        '''
        Move to an absolute position

        Parameters
        ----------
        position: int
            desired position in steps
        '''
        assert False

    @abc.abstractmethod
    def set_velocity(self, axis=1):
        '''
        Set motor velocity

        Parameters
        ----------
        velocity: float
            desired velocity in steps per second
        '''
        assert False


    @abc.abstractmethod
    def stop(self, axis=1):
        assert False

    @abc.abstractmethod
    def deinitialize(self, axis=1):
        assert False

