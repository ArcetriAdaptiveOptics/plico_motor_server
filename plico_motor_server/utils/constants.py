

class Constants:
    APP_NAME = "inaf.arcetri.ao.plico_motor_server"
    APP_AUTHOR = "INAF Arcetri Adaptive Optics"
    THIS_PACKAGE = 'plico_motor_server'

    PROCESS_MONITOR_CONFIG_SECTION = 'processMonitor'
    SERVER_CONFIG_SECTION_PREFIX = 'motor'

    PROCESS_MONITOR_PORT = 8989

    # TODO: must be the same of console_scripts in setup.py
    START_PROCESS_NAME = 'plico_motor_start'
    STOP_PROCESS_NAME = 'plico_motor_stop'
    KILL_ALL_PROCESS_NAME = 'plico_motor_kill_all'
    SERVER_PROCESS_NAME = 'plico_motor_server'
    FAKE_NEWFOCUS8742_PROCESS_NAME = 'plico_motor_fake_newfocus8742'
