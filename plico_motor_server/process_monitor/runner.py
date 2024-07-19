#!/usr/bin/env python

from plico.utils.base_process_monitor_runner import BaseProcessMonitorRunner
from plico_motor_server.utils.constants import Constants

class Runner(BaseProcessMonitorRunner):

    @classmethod
    def server_process_name(cls):
        return Constants.SERVER_PROCESS_NAME

