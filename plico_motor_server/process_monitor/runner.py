#!/usr/bin/env python

from plico.utils.base_process_monitor_runner import BaseProcessMonitorRunner
from plico_motor_server.utils.constants import Constants



class Runner(BaseProcessMonitorRunner):

    RUNNING_MESSAGE = "Monitor of processes is running."

    def __init__(self):
        super().__init__(name='Monitor of processes',
                         server_config_prefix='motor',
                         runner_config_section='processMonitor',
                         server_process_name='plico_motor_server',
                         process_monitor_port=Constants.PROCESS_MONITOR_PORT)

