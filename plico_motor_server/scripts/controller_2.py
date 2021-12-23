#!/usr/bin/env python
import sys
from plico.utils.config_file_manager import ConfigFileManager
from plico_motor_server.controller.runner import Runner
from plico_motor_server.utils.constants import Constants


def main():
    runner = Runner()
    configFileManager = ConfigFileManager(Constants.APP_NAME,
                                          Constants.APP_AUTHOR,
                                          Constants.THIS_PACKAGE)
    configFileManager.installConfigFileFromPackage()
    argv = ['',
            configFileManager.getConfigFilePath(),
            Constants.SERVER_2_CONFIG_SECTION]
    sys.exit(runner.start(argv))


if __name__ == '__main__':
    main()
