import abc
from six import with_metaclass
from plico.utils.decorator import returns


class AbstractMotor(with_metaclass(abc.ABCMeta, object)):

    # -------------
    # Queries

    @abc.abstractmethod
    def name(self):
        assert False

    @abc.abstractmethod
    def position(self):
        assert False

    @abc.abstractmethod
    def steps_per_SI_unit(self):
        assert false

    @abc.abstractmethod
    def was_homed(self):
        assert false

    @abc.abstractmethod
    def type(self):
        assert false

    @abc.abstractmethod
    def is_moving(self):
        assert false

    @abc.abstractmethod
    def last_commanded_position(self):
        assert false

    # --------------
    # Commands

    @abc.abstractmethod
    def home(self):
        assert False

    @abc.abstractmethod
    def move_to(self):
        assert False

    @abc.abstractmethod
    def stop(self):
        assert False

    @abc.abstractmethod
    def deinitialize(self):
        assert False


