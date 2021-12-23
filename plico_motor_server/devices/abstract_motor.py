import abc
from six import with_metaclass
from plico.utils.decorator import returns


class AbstractMotor(with_metaclass(abc.ABCMeta, object)):

    @abc.abstractmethod
    def name(self):
        assert False

    @abc.abstractmethod
    def home(self):
        assert False

    @abc.abstractmethod
    def position(self):
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
