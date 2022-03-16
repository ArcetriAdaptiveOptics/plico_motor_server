

class Constants:
    APP_NAME = "inaf.arcetri.ao.plico_motor_server"
    APP_AUTHOR = "INAF Arcetri Adaptive Optics"
    THIS_PACKAGE = 'plico_motor_server'

    PROCESS_MONITOR_CONFIG_SECTION = 'processMonitor'
    SERVER_1_CONFIG_SECTION = 'motor1'
    SERVER_2_CONFIG_SECTION = 'motor2'
    SERVER_3_CONFIG_SECTION = 'motor3'
    SERVER_4_CONFIG_SECTION = 'motor4'

    # TODO: must be the same of console_scripts in setup.py
    START_PROCESS_NAME = 'plico_motor_start'
    STOP_PROCESS_NAME = 'plico_motor_stop'
    KILL_ALL_PROCESS_NAME = 'plico_motor_kill_all'
    SERVER_1_PROCESS_NAME = 'plico_motor_server_1'
    SERVER_2_PROCESS_NAME = 'plico_motor_server_2'
    SERVER_3_PROCESS_NAME = 'plico_motor_server_3'
    SERVER_4_PROCESS_NAME = 'plico_motor_server_4'
    FAKE_NEWFOCUS8742_PROCESS_NAME = 'plico_motor_fake_newfocus8742'
