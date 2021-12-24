import abc
from six import with_metaclass


class AbstractMotor(with_metaclass(abc.ABCMeta, object)):

    # -------------
    # Queries

    @abc.abstractmethod
    def name(self):
        assert False

    @abc.abstractmethod
    def position(self):
        '''
        Returns
        ------
        position: int
            axis position in steps
        '''
        assert False

    @abc.abstractmethod
    def steps_per_SI_unit(self):
        '''
        Returns
        ------
        steps_per_SI_unit: float
            steps/m if linear motor or steps/rad if rotative motor
        '''
        assert False

    @abc.abstractmethod
    def was_homed(self):
        assert False

    @abc.abstractmethod
    def type(self):
        assert False

    @abc.abstractmethod
    def is_moving(self):
        assert False

    @abc.abstractmethod
    def last_commanded_position(self):
        '''
        Returns
        ------
        last commanded position: int
            last set point in steps
        '''
        assert False

    # --------------
    # Commands

    @abc.abstractmethod
    def home(self):
        '''
        Perform homing / initialization procedure
        '''
        assert False

    @abc.abstractmethod
    def move_to(self):
        '''
        Move to an absolute position

        Parameters
        ----------
        position: int
            desired position in steps
        '''
        assert False

    @abc.abstractmethod
    def stop(self):
        assert False

    @abc.abstractmethod
    def deinitialize(self):
        assert False

