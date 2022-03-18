#!/usr/bin/env python
import sys
from plico.utils.config_file_manager import ConfigFileManager
from plico_motor_server.controller.runner import Runner
from plico_motor_server.utils.constants import Constants


def main():
    runner = Runner()
    sys.exit(runner.start(sys.argv))


if __name__ == '__main__':
    main()
