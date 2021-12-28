import time
from plico.utils.hackerable import Hackerable
from plico.utils.snapshotable import Snapshotable
from plico.utils.stepable import Stepable
from plico.utils.serverinfoable import ServerInfoable
from plico.utils.logger import Logger
from plico.utils.decorator import override, logEnterAndExit
from plico.utils.timekeeper import TimeKeeper
from plico_motor.types.motor_status import MotorStatus


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
    def home(self, axis=1):
        self._motor.home(axis)

    @logEnterAndExit('Entering move_to', 'move_to executed')
    def move_to(self, axis=1, position_in_steps):
        self._motor.move_to(axis, position_in_steps)
        self._logger.notice("moved axis %d to %g" % (axis, position_in_steps))

    @logEnterAndExit('Entering move_by', 'move_by executed')
    def move_by(self, axis=1, delta_position_in_steps):
        curpos = self._motor.position(axis)
        self._motor.move_to(axis, curpos + delta_position_in_steps)

# Not used?
#    def position(self):
#        return self._motor.position()

    def _getMotorStatus(self):
        self._logger.debug('get MotorStatus')
        axisStatus = []
        for i in range(self._motor.naxis):
            axis = i+1
            motorStatus = MotorStatus(
                self._motor.name(),
                self._motor.position(axis),
                self._motor.steps_per_SI_unit(axis),
                self._motor.was_homed(axis),
                self._motor.type(axis),
                self._motor.is_moving(axis),
                self._motor.last_commanded_positionaxis())
            axisStatus.append(motorStatus)
        return axisStatus

    def _publishStatus(self):
        self._rpcHandler.publishPickable(self._statusSocket,
                                         self._getMotorStatus())

    def getSnapshot(self, prefix):
        assert False, 'Should not be used, client uses getStatus instead'

