import os
from plico_motor_server.utils.constants import Constants
from plico_motor_server.utils.process_startup_helper import ProcessStartUpHelper
from plico.utils.starter_script_creator_base import StarterScriptCreatorBase


class StarterScriptCreator(StarterScriptCreatorBase):

    def __init__(self):
        StarterScriptCreatorBase.__init__(self)

    def installExecutables(self):
        psh = ProcessStartUpHelper()

        self._createAStarterScript(
            os.path.join(self._binDir, Constants.START_PROCESS_NAME),
            psh.processProcessMonitorStartUpScriptPath(),
            Constants.PROCESS_MONITOR_CONFIG_SECTION
        )
        self._createAStarterScript(
            os.path.join(self._binDir,
                         Constants.SERVER_1_PROCESS_NAME),
            psh.controllerStartUpScriptPath(),
            Constants.SERVER_1_CONFIG_SECTION
        )
        self._createAStarterScript(
            os.path.join(self._binDir,
                         Constants.SERVER_2_PROCESS_NAME),
            psh.controllerStartUpScriptPath(),
            Constants.SERVER_2_CONFIG_SECTION
        )
        self._createAStarterScript(
            os.path.join(self._binDir, Constants.KILL_ALL_PROCESS_NAME),
            psh.killAllProcessesStartUpScriptPath(),
            'foo'
        )
        self._createAStarterScript(
            os.path.join(self._binDir, Constants.STOP_PROCESS_NAME),
            psh.processProcessMonitorStopScriptPath(),
            'not used'
        )
        self._createAStarterScript(
            os.path.join(self._binDir, Constants.FAKE_NEWFOCUS8742_PROCESS_NAME),
            psh.fakeNewFocus8742ScriptPath(),
            'not used'
        )
