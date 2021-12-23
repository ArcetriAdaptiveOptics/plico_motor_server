import threading
import time
import numpy as np
from plico.utils.hackerable import Hackerable
from plico.utils.snapshotable import Snapshotable
from plico.utils.stepable import Stepable
from plico.utils.serverinfoable import ServerInfoable
from plico.utils.logger import Logger
from plico.utils.decorator import override, logEnterAndExit, synchronized
from plico.utils.timekeeper import TimeKeeper


class MotorController(Stepable,
                      Snapshotable,
                      Hackerable,
                      ServerInfoable):

    def __init__(self,
                 servername,
                 ports,
                 motor,
                 replySocket,
                 publisherSocket,
                 statusSocket,
                 rpcHandler,
                 timeMod=time):
        self._motor = motor
        self._replySocket = replySocket
        self._publisherSocket = publisherSocket
        self._statusSocket = statusSocket
        self._rpcHandler = rpcHandler
        self._timeMod = timeMod
        self._logger = Logger.of('MotorController')
        Hackerable.__init__(self, self._logger)
        ServerInfoable.__init__(self, servername,
                                ports,
                                self._logger)
        self._isTerminated = False
        self._stepCounter = 0
        self._timekeep = TimeKeeper()
        self._motorStatus = None
        self._mutexStatus = threading.RLock()

    @override
    def step(self):
        self._rpcHandler.handleRequest(self, self._replySocket, multi=True)
        self._publishStatus()
        if self._timekeep.inc():
            self._logger.notice(
                'Stepping at %5.2f Hz' % (self._timekeep.rate))
        self._stepCounter += 1

    def getStepCounter(self):
        return self._stepCounter

    def terminate(self):
        self._logger.notice("Got request to terminate")
        try:
            self._motor.stop()
            self._motor.deinitialize()
        except Exception as e:
            self._logger.warn(
                "Could not stop & deinitialize motor: %s" % str(e))
        self._isTerminated = True

    @override
    def isTerminated(self):
        return self._isTerminated

    @logEnterAndExit('Entering home', 'Homing executed')
    def home(self):
        self._motor.home()
        pass

    @logEnterAndExit('Entering move_to', 'move_to executed')
    def move_to(self, position_in_steps):
        self._motor.move_to(position_in_steps)
        with self._mutexStatus:
            self._motorStatus = None

    def move_by(self):
        pass

    def setExposureTime(self, exposureTimeInMilliSeconds):
        self._motor.setExposureTime(exposureTimeInMilliSeconds)
        with self._mutexStatus:
            self._cameraStatus = None

    def _getExposureTime(self):
        return self._getCameraStatus().exposureTimeInMilliSec

    @logEnterAndExit('Entering setBinning',
                     'Executed setBinning')
    def setBinning(self, binning):
        self._motor.setBinning(binning)
        with self._mutexStatus:
            self._cameraStatus = None

    def getBinning(self):
        assert False, 'Should not be used, client uses getStatus instead'

    def getSnapshot(self, prefix):
        assert False, 'Should not be used, client uses status instead'

    @synchronized("_mutexStatus")
    def _getCameraStatus(self):
        if self._cameraStatus is None:
            self._logger.debug('get CameraStatus')
            self._cameraStatus = CameraStatus(
                self._motor.name(),
                self._motor.cols(),
                self._motor.rows(),
                self._motor.dtype(),
                self._motor.getBinning(),
                self._motor.exposureTime(),
                self._motor.getFrameRate())
        return self._cameraStatus

    def _publishStatus(self):
        self._rpcHandler.publishPickable(self._statusSocket,
                                         self._getCameraStatus())

