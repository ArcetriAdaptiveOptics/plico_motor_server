'''
Authors
  - C. Selmi: written in 2022
  
SOURCE: https://github.com/Thorlabs/Motion_Control_Examples/blob/main/Python/Integrated%20Stages/LTS/lts_pythonnet.py#L59

'''
import os
import time
import sys
import clr
import serial
from plico.utils.logger import Logger
from plico.utils.decorator import override
from plico.utils.reconnect import Reconnecting, reconnect
from plico_motor_server.devices.abstract_motor import AbstractMotor
from plico_motor.types.motor_status import MotorStatus

clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.DeviceManagerCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.GenericMotorCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\ThorLabs.MotionControl.IntegratedStepperMotorsCLI.dll")
from Thorlabs.MotionControl.DeviceManagerCLI import *
from Thorlabs.MotionControl.GenericMotorCLI import *
from Thorlabs.MotionControl.IntegratedStepperMotorsCLI import *
from System import Decimal  # necessary for real world units


class LTSThorlabsException(Exception):
    pass

class LTSThorlabsMotor(AbstractMotor):
    '''
    This class allow to control Thorlabs LTS integrated stages motors with python using pythonnet
    '''
    
    def __init__(self, name, serial_number):
        self._name = name
        self.serial_number = serial_number
        self._logger = Logger.of("LTS Stage %s" %self.serial_number)
        self.device = LongTravelStage.CreateLongTravelStage(self.serial_no)
        self._last_commanded_position = None
        self._standar_time_out = 60000 # 60 second timeout
        
    
    def connect(self):
        self.device.Connect(self.serial_no)
        motor_config = self.device.LoadMotorConfiguration(self.serial_no)
        
        self.device.StartPolling(250)
        self.device.EnableDevice()
    
    def identifyDevice(self):
        self.device.IdentifyDevice()
    
    def homing(self):
        self.device.Home(self._standar_time_out)

    def _get_position(self):
        pos = Decimal.ToDouble(self.device.get_DevicePosition())
        return pos
    
    def _set_position(self, absolute_pos_in_mm):
        new_pos = Decimal(absolute_pos_in_mm)
        self.device.MoveTo(new_pos, self._standar_time_out)
        
    def _check_position(self, position):
        ''' Function for checking if the required position is inside the stage range 0-150 [mm]
        '''
        min_acceptable_value = 0.0
        max_acceptable_value = 150.0
        if position < min_acceptable_value:
            raise LTSThorlabsException('Negative value for the required position are not allow.')
        elif position > max_acceptable_value:
            raise LTSThorlabsException('The required value for the position exceed the stage range. The maximum value allow is 150 mm')

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
        
        '''
        actual_position = self._get_position()
        self._logger.debug(
            'Current position = %f [mm]' % actual_position)
        return actual_position

    @override
    def steps_per_SI_unit(self, axis):
        ''' Number of steps/m
        '''
        pass

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
        ''' To be implemented our homing command 
        '''
        pass
    
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
    def stop(self, axis):
        pass

    @override
    def deinitialize(self, axis):
        raise LTSThorlabsException('Deinitialize command is not supported.')


    
    
    
    def search_devices():
        DeviceManagerCLI.BuildDeviceList()
        return DeviceManagerCLI.GetDeviceList()
