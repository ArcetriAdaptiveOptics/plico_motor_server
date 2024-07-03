
'''
Authors
  - C. Selmi: written in 2024
'''
import clr
from plico.utils.logger import Logger
from plico.utils.decorator import override
from plico.utils.reconnect import Reconnecting, reconnect
from plico_motor_server.devices.abstract_motor import AbstractMotor
from plico_motor.types.motor_status import MotorStatus

clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.DeviceManagerCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.GenericMotorCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\ThorLabs.MotionControl.FilterFlipperCLI.dll")
from Thorlabs.MotionControl.DeviceManagerCLI import *
from Thorlabs.MotionControl.GenericMotorCLI import *
from Thorlabs.MotionControl.FilterFlipperCLI import *
from System import Decimal, UInt32

class MFF10xThorlabsException(Exception):
    pass

class MFF10xThorlabsMotor(AbstractMotor):
    '''
    This class allow to control Thorlabs MFF10x filter flipper with python using pythonnet.
    '''
    
    def __init__(self, name, serial_number):
        self._name = name
        self.naxis = 1
        self.serial_no = serial_number
        self._logger = Logger.of("MFF10x Filter Flipper %s" %self.serial_no)
        self.connect()
        self._last_commanded_position = None
        self._standar_time_out = 60000 # 60 second timeout
        self._deviceSettings = self.device.FilterFlipperDeviceSettings
        
    def connect(self):
        '''
        Connection to the device requires all of these nonseparable commands.
        '''
        self.device = FilterFlipper.CreateFilterFlipper(self.serial_no)
        DeviceManagerCLI.BuildDeviceList() #without this command the connection fails
        self.device.Connect(self.serial_no)
        
        self.device.StartPolling(250)
        self.enable()
        
    def enable(self):
        self.device.EnableDevice()
        c = DeviceConfiguration.DeviceSettingsUseOptionType
        self.device.GetDeviceConfiguration(self.serial_no, c.UseDeviceSettings)
    
    def identifyDevice(self):
        '''
        Device identification causes the enable LED to blink.
        '''
        self.device.IdentifyDevice()
    
    def homing(self):
        '''
        The standard homing position is zero and is equivalent to the 1 position (horizontal filter)
        '''
        self.device.Home(self._standar_time_out)
        
    def _get_position(self):
        return self.device.get_Position()
    
    def _set_position(self, position):
        '''
        Parameters
        ----------
        position: int
        	1 for horizontal position and 2 for vertical position
        '''
        self.device.SetPosition(UInt32(position), 60000)
        
    def get_transitTime(self):
        '''
        The time taken to get from one position to other in milliseconds, range 10 to 100000.
        '''
        self.device.GetSettings(self._deviceSettings)
        transit_time = self._deviceSettings.get_FilterFlipper().get_TransitTime()
        return transit_time
    
    def set_transitTime(self, time_in_ms):
        self.device.GetSettings(self._deviceSettings)
        self._deviceSettings.get_FilterFlipper().set_TransitTime(time_in_ms)
        self.device.SetSettings(self._deviceSettings, False)
    
    def _stop(self):
        self.device.Stop(0) #wait timeout set to zero --> will return immediately
    
    def disable(self):
        self.device.DisableDevice()
        
    def disconnect(self):
        self.device.StopPolling()
        self.device.Disconnect()
        
## Per classe astratta ###
    @override
    def name(self):
        '''
        Returns
        -------
        name: string
            filter name
        '''
        return self._name

    @override
    def position(self, axis):
        '''
        Returns
        -------
        actual_position: float
            return the actual position of the filter flipper
        '''
        actual_position = self._get_position()
        self._logger.debug(
            'Current position = %f ' % actual_position)
        return actual_position

    @override
    def velocity(self, axis):
        '''
        Returns
        -------
        velocity: float
            motor velocity in steps/s
        '''
        transit_time = self.get_transitTime()
        if transit_time != 0:
            velocity = 1000 / transit_time
        else:
            velocity = 0.0
        self._logger.debug(
            'Velocity = %f [mm/s]' % velocity)
        return velocity

    @override
    def steps_per_SI_unit(self, axis):
        ''' Number of steps/m
        '''
        return 1

    @override
    def was_homed(self, axis):
        return True

    @override
    def type(self, axis):
        '''
        Returns
        -------
        type: string
             type of motor controller
        '''
        return MotorStatus.TYPE_LINEAR

    @override
    def is_moving(self, axis):
        return False

    @override
    def last_commanded_position(self, axis):
        '''
        Returns
        ------
        last commanded position: float
            last commanded position
        '''
        return self._last_commanded_position

    @override
    def naxes(self):
        '''
        Returns
        ------
        naxes: int
            number of motor axes
        '''
        return self.naxis
    
    @override
    def home(self, axis):
        self.homing()
    
    @override
    def move_to(self, axis, pos):
        '''
        Parameters
        ----------
            pos: int
              1 for horizontal position and 2 for vertical position 
        '''
        self._set_position(pos)
        self._last_commanded_position = pos

    @override
    def set_velocity(self, axis, velocity):
        '''
        Parameters
        ----------
        velocity: float
            velocity in step/s
        '''
        if velocity < 0.01:
            self._logger.error('Velocity %s steps/s is too low, minimum value is 0.01 steps/s' % velocity)
            velocity = 0.01

        if velocity > 100:
            self._logger.error('Velocity %s steps/s is too high, maximum value is 100 steps/s' % velocity)
            velocity = 100

        self.set_transitTime(int(1000 // velocity))

    @override
    def stop(self, axis):
        self._stop()

    @override
    def deinitialize(self, axis):
        raise MFF10xThorlabsException('Deinitialize command is not supported.')


    
    
    
def search_devices():
    DeviceManagerCLI.BuildDeviceList()
    for i in range(0, len(DeviceManagerCLI.GetDeviceList())):
        print(DeviceManagerCLI.GetDeviceList()[i])
    return DeviceManagerCLI.GetDeviceList()        