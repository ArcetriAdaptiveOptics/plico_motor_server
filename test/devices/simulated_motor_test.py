#!/usr/bin/env python
import unittest
import logging
from plico.utils.logger import Logger
from plico_motor_server.devices.simulated_motor import SimulatedMotor


class SimulatedAuxiliaryCameraTest(unittest.TestCase):

    def setUp(self):
        self._setUpLogging()
        self._motor = SimulatedMotor()

    def tearDown(self):
        self._motor.raise_exception_on_deinitialize(False)
        self._motor.deinitialize()

    def _setUpLogging(self):
        FORMAT = '%(asctime)s %(levelname)s %(message)s'
        logging.basicConfig(level=logging.DEBUG, format=FORMAT)
        self._logger = Logger.of(self.__class__.__name__)

    def test_move_to(self):
        self._motor.move_to(123)
        self.assertEqual(123, self._motor.position())


if __name__ == "__main__":
    unittest.main()
