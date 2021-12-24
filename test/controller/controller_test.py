#!/usr/bin/env python
import unittest
from plico_motor_server.controller.controller import MotorController
from plico_motor_server.devices.simulated_motor import SimulatedMotor


class MyReplySocket():
    pass


class MyPublisherSocket():
    pass


class MyRpcHandler():

    def __init__(self):
        self._publish = {}

    def handleRequest(self, obj, socket, multi):
        pass

    def publishPickable(self, socket, anObject):
        self._publish[socket] = anObject

    def getLastPublished(self, socket):
        return self._publish[socket]

    def sendCameraFrame(self, socket, frame):
        self.publishPickable(socket, frame)


class MotorControllerTest(unittest.TestCase):

    def setUp(self):
        self._motor = SimulatedMotor()
        self._rpcHandler = MyRpcHandler()
        self._replySocket = MyReplySocket()
        self._publisherSocket = MyPublisherSocket()
        self._statusSocket = MyPublisherSocket()
        self._serverName = 'pippo'
        self._ports = 'foo'
        self._ctrl = MotorController(
            self._serverName,
            self._ports,
            self._motor,
            self._replySocket,
            self._publisherSocket,
            self._statusSocket,
            self._rpcHandler)

    def tearDown(self):
        self._motor.raise_exception_on_deinitialize(False)
        self._motor.deinitialize()

    def test_publishes_status(self):
        self._ctrl.step()
        status = self._rpcHandler.getLastPublished(
            self._statusSocket)
        self.assertEqual(self._motor.position(),
                         status.position)
        self.assertEqual(self._motor.is_moving(),
                         status.is_moving)
        self.assertEqual(self._motor.steps_per_SI_unit(),
                         status.steps_per_SI_unit)
        self.assertEqual(self._motor.was_homed(),
                         status.was_homed)

    def test_new_status_is_published_at_every_step(self):
        self._ctrl.step()
        status1 = self._rpcHandler.getLastPublished(
            self._statusSocket)
        self._ctrl.step()
        status2 = self._rpcHandler.getLastPublished(
            self._statusSocket)
        self.assertNotEqual(status1, status2)

    def test_terminate(self):
        self._motor.raise_exception_on_deinitialize(True)
        self._ctrl.terminate()
        self.assertTrue(self._ctrl.isTerminated())

    def test_home(self):
        self._ctrl.home()
        self.assertTrue(self._motor.was_homed())

    def test_move_to_by(self):
        self._ctrl.move_to(123)
        self.assertEqual(123, self._motor.position())
        self._ctrl.move_by(-10)
        self.assertEqual(113, self._motor.position())


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
