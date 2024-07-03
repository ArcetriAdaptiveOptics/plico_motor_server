'''
Authors
  - C. Selmi: written in 2024
'''
from plico.utils.logger import Logger
from plico.utils.decorator import override
from plico.utils.reconnect import Reconnecting, reconnect
from plico_motor_server.devices.abstract_motor import AbstractMotor
from plico_motor.types.motor_status import MotorStatus

import clr
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.DeviceManagerCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.GenericMotorCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\ThorLabs.MotionControl.KCube.DCServoCLI.dll")
from Thorlabs.MotionControl.DeviceManagerCLI import *
from Thorlabs.MotionControl.GenericMotorCLI import *
from Thorlabs.MotionControl.KCube.DCServoCLI import *
from System import Decimal

class KDC101ThorlabsException(Exception):
    pass

class KDC101ThorlabsMotor(AbstractMotor):
    '''
    This class allow to control Thorlabs KDC 101 KCube with python using pythonnet.
    The motor controlled by the KCube is Z912B linear actuator --> position command checker use this range in position (0 to 12 mm)
    '''
    
    def __init__(self, name, serial_number):
        self._name = name
        self.naxis = 1
        self.serial_no = serial_number
        self._logger = Logger.of("KDC101 KCube %s" %self.serial_no)
        self.connect()
        self._last_commanded_position = None
        self._standar_time_out = 60000 # 60 second timeout
        
    def connect(self):
        '''
        Connection to the device requires all of these nonseparable commands.
        '''
        self.device = KCubeDCServo.CreateKCubeDCServo(self.serial_no)
        DeviceManagerCLI.BuildDeviceList() #without this command the connection fails
        self.device.Connect(self.serial_no)
        m_config = self.device.LoadMotorConfiguration(self.serial_no, DeviceConfiguration.DeviceSettingsUseOptionType.UseFileSettings)
        
        self.device.StartPolling(250)
        self.device.EnableDevice()
        
    def enable(self):
        self.device.EnableDevice()
    
    def identifyDevice(self):
        '''
        Device identification causes the enable LED to blink.
        '''
        self.device.IdentifyDevice()
    
    def homing(self):
        '''
        The standard homing position is zero.
        '''
        self.device.Home(self._standar_time_out)
        
    def _get_position(self):
        ''' Absolute position in mm
        '''
        pos = Decimal.ToDouble(self.device.get_DevicePosition())
        return pos
    
    def _set_position(self, absolute_pos_in_mm):
        ''' The same command as device.SetMoveRelativeDistance + device.MoveAbsolute
        '''
        new_pos = Decimal(absolute_pos_in_mm)
        self.device.MoveTo(new_pos, self._standar_time_out)
    
    def _move_by(self, step_in_mm):
        self.device.SetMoveRelativeDistance(Decimal(step_in_mm))
        self.device.MoveRelative(self._standar_time_out)
        
    def _check_position(self, position):
        ''' Function for checking if the required position is inside the stage range 0-12 [mm] defined by the Z912B linear actuator.
        '''
        min_acceptable_value = 0.0
        max_acceptable_value = 12.0
        if position < min_acceptable_value:
            raise KDC101ThorlabsException('Negative value for the required position are not allow.')
        elif position > max_acceptable_value:
            raise KDC101ThorlabsException('The required value for the position exceed the stage range. The maximum value allow is 12 mm')
    
    def _stop(self):
        self.device.Stop(0) #wait timeout set to zero --> will return immediately

    def disable(self):
        self.device.DisableDevice()
        
    def disconnect(self):
        self.device.StopPolling()
        self.device.Disconnect()
    
    def get_acceleration(self):
        '''
        Returns
        -------
        acceleration: float [mm/s^2]
        '''
        velocity_params = self.device.GetVelocityParams()
        acceleration = Decimal.ToDouble(velocity_params.get_Acceleration())
        return acceleration
        
    def set_acceleration(self, value):
        ''' Set the motor velocity
        Parameters
        ----------
        value: float [mm/s^2]
        '''
        velocity_params = self.device.GetVelocityParams()
        velocity_params.set_Acceleration(Decimal(value))
        self.device.SetVelocityParams(velocity_params)

    def get_max_velocity(self):
        '''
        Returns
        -------
        max_vel: float [mm/s]
        '''
        velocity_params = self.device.GetVelocityParams()
        max_vel = Decimal.ToDouble(velocity_params.get_MaxVelocity())
        return max_vel
    
    def set_max_velocity(self, value):
        ''' Set the motor velocity
        Parameters
        ----------
        value: float [mm/s]
        '''
        velocity_params = self.device.GetVelocityParams()
        velocity_params.set_MaxVelocity(Decimal(value))
        self.device.SetVelocityParams(velocity_params)
    
    def get_min_velocity(self):
        '''
        Returns
        -------
        min_vel: float [nm/s]
        '''
        velocity_params = self.device.GetVelocityParams()
        min_vel = Decimal.ToDouble(velocity_params.get_MinVelocity())
        return min_vel
    
    def set_min_velocity(self, value):
        '''
        Parameters
        ----------
        value: float [nm/s]
        '''
        velocity_params = self.device.GetVelocityParams()
        velocity_params.set_MinVelocity(Decimal(value))
        self.device.SetVelocityParams(velocity_params)
   
 
## Per classe astratta ###
    @override
    def name(self):
        '''
        Returns
        -------
        name: string
            motor name
        '''
        return self._name

    @override
    def position(self, axis):
        '''
        Returns
        -------
        actual_position: float
            return the actual position of the motor in mm
        '''
        actual_position = self._get_position()
        self._logger.debug(
            'Current position = %f [mm]' % actual_position)
        return actual_position

    @override
    def velocity(self, axis):
        '''
        Returns
        -------
        velocity: float
            motor velocity in mm/s
        '''
        velocity = self.get_max_velocity()
        self._logger.debug(
            'Velocity = %f [mm/s]' % velocity)
        return velocity

    @override
    def steps_per_SI_unit(self, axis):
        ''' Number of steps/m
        '''
        return 1000

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
            pos: float
               absolute position in mm
        '''
        self._check_position(pos)
        self._set_position(pos)
        self._last_commanded_position = pos

    @override
    def set_velocity(self, axis, velocity):
        '''
        Parameters
        ----------
        velocity: float
            velocity in mm/sec
        '''
        self.set_max_velocity(velocity)

    @override
    def stop(self, axis):
        self._stop()

    @override
    def deinitialize(self, axis):
        raise KDC101ThorlabsException('Deinitialize command is not supported.')


    
    
    
def search_devices():
    DeviceManagerCLI.BuildDeviceList()
    for i in range(0, len(DeviceManagerCLI.GetDeviceList())):
        print(DeviceManagerCLI.GetDeviceList()[i])
    return DeviceManagerCLI.GetDeviceList()
      