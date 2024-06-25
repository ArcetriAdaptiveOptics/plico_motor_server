import os
import sys
import subprocess
import shutil
import unittest
import logging
import numpy as np
from test.test_helper import TestHelper, Poller, MessageInFileProbe, \
    ExecutionProbe
from plico.utils.configuration import Configuration
from plico.rpc.zmq_remote_procedure_call import ZmqRemoteProcedureCall
from plico.utils.logger import Logger
from plico.rpc.sockets import Sockets
from plico.rpc.zmq_ports import ZmqPorts
from plico.client.serverinfo_client import ServerInfoClient
from plico_motor_server.utils.constants import Constants
from plico_motor_server.utils.starter_script_creator import \
    StarterScriptCreator
from plico_motor_server.utils.process_startup_helper import \
    ProcessStartUpHelper
from plico_motor_server.process_monitor.runner import Runner as \
    ProcessMonitorRunner
from plico_motor.client.motor_client import MotorClient
from plico_motor.client.snapshot_entry import SnapshotEntry
from plico_motor_server.controller.runner import Runner
from plico_motor_server.devices.picomotor import PicomotorException
from plico_motor_server.devices.fake_newfocus8742 import \
    NewFocus8742ServerProtocol


@unittest.skipIf(sys.platform == "win32",
                 "Integration test doesn't run on Windows. Fix it!")
class IntegrationTest(unittest.TestCase):

    TEST_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                            "./tmp/")
    LOG_DIR = os.path.join(TEST_DIR, "log")
    CONF_FILE = 'test/integration/conffiles/plico_motor_server.conf'
    CALIB_FOLDER = 'test/integration/calib'
    CONF_SECTION = Constants.PROCESS_MONITOR_CONFIG_SECTION
    SERVER_LOG_PATH = os.path.join(LOG_DIR, "%s.log" % CONF_SECTION)
    BIN_DIR = os.path.join(TEST_DIR, "apps", "bin")
    SOURCE_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                              "../..")

    def setUp(self):
        self._setUpBasicLogging()
        self.server = None
        self._wasSuccessful = False

        self._removeTestFolderIfItExists()
        self._makeTestDir()
        self.configuration = Configuration()
        self.configuration.load(self.CONF_FILE)
        self.rpc = ZmqRemoteProcedureCall()

        calibrationRootDir = self.configuration.calibrationRootDir()
        self._setUpCalibrationTempFolder(calibrationRootDir)

    def _setUpBasicLogging(self):
        logging.basicConfig(level=logging.DEBUG)
        self._logger = Logger.of('Integration Test')

    def _makeTestDir(self):
        os.makedirs(self.TEST_DIR)
        os.makedirs(self.LOG_DIR)
        os.makedirs(self.BIN_DIR)

    def _setUpCalibrationTempFolder(self, calibTempFolder):
        shutil.copytree(self.CALIB_FOLDER,
                        calibTempFolder)

    def _removeTestFolderIfItExists(self):
        if os.path.exists(self.TEST_DIR):
            shutil.rmtree(self.TEST_DIR)

    def tearDown(self):
        TestHelper.dumpFileToStdout(self.SERVER_LOG_PATH)

        if self.server is not None:
            TestHelper.terminateSubprocess(self.server)

        if self.fakenewfocus8742 is not None:
            TestHelper.terminateSubprocess(self.fakenewfocus8742)

        if self._wasSuccessful:
            self._removeTestFolderIfItExists()

    def _createStarterScripts(self):
        ssc = StarterScriptCreator()
        ssc.setInstallationBinDir(self.BIN_DIR)
        ssc.setPythonPath(self.SOURCE_DIR)
        ssc.setConfigFileDestination('$1') # Allow config file to be a script parameter
        ssc.installExecutables()

    def _startProcesses(self):
        psh = ProcessStartUpHelper()
        serverLog = open(os.path.join(self.LOG_DIR, "server.out"), "wb")
        self.server = subprocess.Popen(
            [psh.processProcessMonitorStartUpScriptPath(),
             self.CONF_FILE,
             self.CONF_SECTION],
            stdout=serverLog, stderr=serverLog)
        Poller(5).check(MessageInFileProbe(
            ProcessMonitorRunner.RUNNING_MESSAGE, self.SERVER_LOG_PATH))

    def _startFakeNewFocus8742(self):
        psh = ProcessStartUpHelper()
        logPath = os.path.join(self.LOG_DIR, "newfocus8742.out")
        serverLog = open(logPath, "wb")
        self.fakenewfocus8742 = subprocess.Popen(
            [psh.fakeNewFocus8742ScriptPath(),
             self.CONF_FILE,
             self.CONF_SECTION],
            stdout=serverLog, stderr=serverLog)
        Poller(5).check(MessageInFileProbe(
            NewFocus8742ServerProtocol.RUNNING_MESSAGE, logPath))

    def _testProcessesActuallyStarted(self):
        controllerLogFile = os.path.join(
            self.LOG_DIR,
            '%s%d.log' % (Constants.SERVER_CONFIG_SECTION_PREFIX, 1))
        Poller(5).check(MessageInFileProbe(
            Runner.RUNNING_MESSAGE, controllerLogFile))
        controller2LogFile = os.path.join(
            self.LOG_DIR,
            '%s%d.log' % (Constants.SERVER_CONFIG_SECTION_PREFIX, 2))
        Poller(5).check(MessageInFileProbe(
            Runner.RUNNING_MESSAGE, controller2LogFile))

    def _buildClients(self):
        ports1 = ZmqPorts.fromConfiguration(
            self.configuration,
            '%s%d' % (Constants.SERVER_CONFIG_SECTION_PREFIX, 1))
        self.client1 = MotorClient(
            self.rpc, Sockets(ports1, self.rpc))
        ports2 = ZmqPorts.fromConfiguration(
            self.configuration,
            '%s%d' % (Constants.SERVER_CONFIG_SECTION_PREFIX, 2))
        self.client2Axis = 2
        self.client2 = MotorClient(
            self.rpc, Sockets(ports2, self.rpc), axis=self.client2Axis)
        self.clientAll = ServerInfoClient(
            self.rpc,
            Sockets(ZmqPorts('localhost', Constants.PROCESS_MONITOR_PORT), self.rpc).serverRequest(),
            self._logger)

    def _check_backdoor(self):
        self.client1.execute(
            "import numpy as np; "
            "self._myarray= np.array([1, 2])")
        self.assertEqual(
            repr(np.array([1, 2])),
            self.client1.eval("self._myarray"))
        self.client1.execute("self._foobar= 42")
        self.assertEqual(
            "42",
            self.client1.eval("self._foobar"))

    def _test_get_snapshot(self):
        snapshot = self.client2.snapshot('aa')
        snKey = 'aa.%s' % SnapshotEntry.MOTOR_NAME
        self.assertEqual('My 4 axis Picomotor', snapshot[snKey])

    def _test_server_info(self):
        serverInfo = self.client1.serverInfo()
        self.assertEqual('motor 1 server',
                         serverInfo.name)
        self.assertEqual('localhost', serverInfo.hostname)

    def _test_at_boot_is_not_homed(self):
        status = self.client1.status()
        self.assertFalse(status.was_homed)

    def _test_home_and_get_position(self):
        self.client1.home()
        Poller(3).check(ExecutionProbe(
            lambda: self.assertTrue(self.client1.status().was_homed)))
        self.assertEqual(self.client1.position(), 0)

    def _test_picomotor_raise_exception_on_home(self):
        self.assertRaises(PicomotorException, self.client2.home)

    def _test_picomotor_raise_exception_on_set_velocity(self):
        self.assertRaises(PicomotorException, self.client2.set_velocity)

    def _test_move_to(self):
        self.client1.move_to(123)
        self.client2.move_to(-34)
        Poller(3).check(ExecutionProbe(
            lambda: self.assertEqual(123,
                                     self.client1.position())))
        Poller(3).check(ExecutionProbe(
            lambda: self.assertEqual(int(-34),
                                     self.client2.position())))

    def _test_move_by(self):
        self.client1.move_by(-23)
        self.client2.move_by(10)
        Poller(3).check(ExecutionProbe(
            lambda: self.assertEqual(100, self.client1.position())))
        Poller(3).check(ExecutionProbe(
            lambda: self.assertEqual(-24, self.client2.position())))

    def _test_set_velocity(self):
        self.client1.set_velocity(42)
        Poller(3).check(ExecutionProbe(
            lambda: self.assertEqual(42,
                                     self.client1.velocity())))

    def _test_info(self):
        with open('/tmp/info.txt', 'w') as f:
            info = self.clientAll.serverInfo()
            f.write(str(info))

    def test_main(self):
        self._buildClients()
        self._createStarterScripts()
        self._startFakeNewFocus8742()
        self._startProcesses()
        self._testProcessesActuallyStarted()
        self._test_at_boot_is_not_homed()
        self._test_home_and_get_position()
        self._test_picomotor_raise_exception_on_home()
        self._test_move_to()
        self._test_move_by()
        self._test_set_velocity()
        self._test_get_snapshot()
        self._test_server_info()
        self._check_backdoor()
        self._test_info()
        self._wasSuccessful = True


if __name__ == "__main__":
    unittest.main()
