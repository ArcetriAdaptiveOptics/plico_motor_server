import os


class ProcessStartUpHelper(object):

    def __init__(self):
        self._moduleRoot = 'plico_motor_server'

    def controllerStartUpScriptPath(self):
        return os.path.join(self._moduleRoot,
                            'scripts',
                            'controller.py')

    def killAllProcessesStartUpScriptPath(self):
        return os.path.join(self._moduleRoot,
                            'utils',
                            'plico_motor_kill_processes.py')

    def processProcessMonitorStartUpScriptPath(self):
        return os.path.join(self._moduleRoot,
                            'process_monitor',
                            'plico_motor_run_process_monitor.py')

    def processProcessMonitorStopScriptPath(self):
        return os.path.join(self._moduleRoot,
                            'utils',
                            'plico_motor_server_stop.py')

    def fakeNewFocus8742ScriptPath(self):
        return os.path.join(self._moduleRoot,
                            'devices',
                            'fake_newfocus8742.py')
