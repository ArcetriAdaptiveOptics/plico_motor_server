#!/usr/bin/env python
import logging
from plico.utils.kill_process_by_name import killProcessByName
from plico_motor_server.utils.constants import Constants


def main():
    logging.basicConfig(level=logging.INFO)
    processNames = [Constants.START_PROCESS_NAME,
                    Constants.SERVER_PROCESS_NAME,
                    ]

    for each in processNames:
        killProcessByName(each)
