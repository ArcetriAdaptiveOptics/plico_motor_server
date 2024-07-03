#!/usr/bin/env python
import unittest
import logging
from plico.utils.logger import Logger
from plico_motor_server.devices.simulated_motor import SimulatedMotor


class SimulatedMotorTest(unittest.TestCase):

    def setUp(self):
        self._setUpLogging()
        self._motor = SimulatedMotor()

    def tearDown(self):
        self._motor.raise_exception_on_deinitialize(False)
        self._motor.deinitialize(1)

    def _setUpLogging(self):
        FORMAT = '%(asctime)s %(levelname)s %(message)s'
        logging.basicConfig(level=logging.DEBUG, format=FORMAT)
        self._logger = Logger.of(self.__class__.__name__)

    def test_move_to(self):
        self._motor.move_to(1, 123)
        self.assertEqual(123, self._motor.position(1))

    def test_velocity(self):
        self._motor.set_velocity(1, 987.6)
        self.assertEqual(987.6, self._motor.velocity(1))


if __name__ == "__main__":
    unittest.main()
