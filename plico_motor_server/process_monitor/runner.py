#!/usr/bin/env python

from plico.utils.base_process_monitor_runner import BaseProcessMonitorRunner


class Runner(BaseProcessMonitorRunner):

    RUNNING_MESSAGE = 'Monitor of plico_motor processes is running'
    def __init__(self):
        super().__init__(runner_config_section='processMonitor',
                         server_config_prefix='motor',
                         server_process_name='plico_motor_server')

