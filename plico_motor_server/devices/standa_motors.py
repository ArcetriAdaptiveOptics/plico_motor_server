'''
Authors
  - C. Selmi: written in July 2023
'''
import os
from ctypes import *
from plico_motor_server.devices.abstract_motor import AbstractMotor
from plico.utils.decorator import override
from plico_motor.types.motor_status import MotorStatus
from plico.utils.logger import Logger

import libximc as pyximc
from ctypes import c_int, byref

class StandaStageException(Exception):
    pass

class StandaStage(AbstractMotor):
    '''
    Class to control standa 8SMC5-USB motor using driver standa 8smc4-5 and the pyximc library.
    Tested whit 8MT30-50, 8MBM24-2-2
    '''
    
    def __init__(self, name, usb_port_name, speed):
        self._open_name = usb_port_name
        self._deviceId = pyximc.lib.open_device(self._open_name)
        self._logger = Logger.of("Standa Stage %s" %self._deviceId)
        self._name = name
        self.naxis = 1
        self.microstep_mode_frac = self.get_microstep_mode()
        self.step_per_rev = self.get_step_per_rev()
        self.speed = self.set_speed(speed)
        self.accel = self.get_acceleration()
        self.decel = self.get_deceleration()
        self._last_commanded_position = None

    def _close(self):
        pyximc.lib.close_device(byref(c_int(self._deviceId)))

    def get_device_info(self):
        ''' Some informations
        '''
        print('Device = %i' %self._deviceId)
        #print('Device model = %s' %self._model)
        print('Sub step fraction = %i' %self.microstep_mode_frac)
        print('Step per revolution = %i' %self.step_per_rev)

    def get_microstep_mode(self):
        ''' return the microstep mode frac number
        '''
        eng = pyximc.engine_settings_t()
        result = pyximc.lib.get_engine_settings(self._deviceId, pyximc.byref(eng))
        self._check_result(result)
        code = eng.MicrostepMode
        if code == 9:
            microstep_mode_frac = 256
        elif code == 8:
            microstep_mode_frac = 128
        elif code == 7:
            microstep_mode_frac = 64
        else:
            microstep_mode_frac = 'Not available'
            print('Read the file 8MT30-50.py, line 92')
        return microstep_mode_frac

    def get_step_per_rev(self):
        '''
        '''
        eng = pyximc.engine_settings_t()
        result = pyximc.lib.get_engine_settings(self._deviceId, pyximc.byref(eng))
        self._check_result(result)
        return eng.StepsPerRev

    def _get_position(self):
        '''
        Returns
        -------
            n_step: int [step related to step_per_rev]
                number of full step of the motor
            n_ustep: int [step related to microstep_mode_frac]
                number of step subdivision of the motor
        '''
        x_pos = pyximc.get_position_t()
        result = pyximc.lib.get_position(self._deviceId, pyximc.byref(x_pos))
        #print("Position: {0} steps, {1} microsteps".format(x_pos.Position, x_pos.uPosition))
        self._check_result(result)
        n_step = x_pos.Position
        n_ustep = x_pos.uPosition
        return n_step, n_ustep

    def move_by(self, delta_step, delta_ustep):
        '''
        Parameters
        ----------
            delta_step: int
                number of full step of the motor
            delta_ustep: int
                number of step subdivision of the motor (Microstep size and the range of valid values
                for this field depend on selected step division mode)
        '''
        result = pyximc.lib.command_movr(self._deviceId, delta_step, delta_ustep)
        self._check_result(result)
        self._wait_for_stop()
        n_step, n_ustep = self._get_position()
        print("Position: {0} steps, {1} microsteps".format(n_step, n_ustep))

    def _wait_for_stop(self):
        result = pyximc.lib.command_wait_for_stop(self._deviceId, 1)
        while result != pyximc.Result.Ok:
            result = pyximc.lib.command_wait_for_stop(self._deviceId, 1)

    def _get_move_settings(self):
        mvst = pyximc.move_settings_t()
        result = pyximc.lib.get_move_settings(self._deviceId, pyximc.byref(mvst))
        self._check_result(result)
        return mvst

    def get_speed(self):
        mvst = self._get_move_settings()
        self.speed = mvst.Speed
        return self.speed

    def set_speed(self, new_speed):
        '''
        Parameters
        ----------
        new_speed: int
              Target speed (for stepper motor: steps/s, for DC: rpm).
              Range: 0..100000
        '''
        mvst = self._get_move_settings()
        mvst.Speed = int(new_speed)
        result = pyximc.lib.set_move_settings(self._deviceId, pyximc.byref(mvst))
        self._check_result(result)
        return self.get_speed()

    def get_acceleration(self):
        mvst = self._get_move_settings()
        self.accel = mvst.Accel
        return self.accel

    def set_acceleration(self, new_accel):
        mvst = self._get_move_settings()
        mvst.Accel = int(new_accel)
        result = pyximc.lib.set_move_settings(self._deviceId, pyximc.byref(mvst))
        self._check_result(result)
        self.get_acceleration()

    def get_deceleration(self):
        mvst = self._get_move_settings()
        self.decel = mvst.Decel
        return self.decel

    def set_deceleration(self, new_decel):
        #mvst = pyximc.move_settings_t()
        mvst = self._get_move_settings()
        mvst.Decel = int(new_decel)
        result = pyximc.lib.set_move_settings(self._deviceId, pyximc.byref(mvst))
        self._check_result(result)
        self.get_deceleration()

    def set_homing_postion(self, home_pos, home_upos):
        ''' Set the new zero position
        '''
        self.move_to(home_pos, home_upos)
        pyximc.lib.command_zero(self._deviceId)
        print('Zero position updated')

    def move_forever_left(self):
        ''' Move to left until the end of the range
        '''
        pyximc.lib.command_left(self._deviceId)

    def move_forever_right(self):
        ''' Move to right until the end of the range
        '''
        pyximc.lib.command_right(self._deviceId)

    def _check_result(self, result):
        if result == pyximc.Result.Ok:
            pass
        elif result == pyximc.Result.Error:
            raise StandaStageException('Generic error: command failed')
        elif result == pyximc.Result.ValueError:
            raise StandaStageException('Value Error: invalid range')

    def _steps2mm(self, step, ustep):
        mmstep = step/self.step_per_rev *0.25
        mmustep = ustep/self.microstep_mode_frac/self.step_per_rev *0.25
        pos = mmstep + mmustep
        return pos
    
    def _mm2steps(self, mm):
        aa = mm/.25*self.step_per_rev 
        steps = int(aa)
        usteps = int((aa - steps)*self.microstep_mode_frac)
        return steps, usteps


### Per classe astratta ###
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
        n_ustep: number of microsteps
        '''
        step, ustep = self._get_position()
        self._logger.debug(
            'Current position (step, ustep) = %d, %d' % (step, ustep))
        return step*self.microstep_mode_frac + ustep

    @override
    def steps_per_SI_unit(self, axis):
        ''' Number of steps/m
        '''
        return self.step_per_rev * self.microstep_mode_frac /0.25

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
        last commanded position: int
            last number commanded position
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
        ''' Different from pyximc.lib.command_home() 
        '''
        self.move_to(axis, 0)
    
    @override
    def move_to(self, axis, upos):
        '''
        Parameters
        ----------
            upos: int
                absolute position in microsteps
        '''
        step = upos // self.microstep_mode_frac
        ustep = upos - step * self.microstep_mode_frac
        result = pyximc.lib.command_move(self._deviceId, step, ustep)
        self._check_result(result)
        self._wait_for_stop()
        n_step, n_ustep = self._get_position()
        print("Position: {0} steps, {1} microsteps".format(n_step, n_ustep))
        self._last_commanded_position = upos

    @override
    def set_velocity(self, axis, velocity):
        '''
        Parameters
        ----------
        new_speed: int
              Target speed (for stepper motor: steps/s, for DC: rpm).
              Range: 0..100000
        '''
        self.set_speed(velocity)

    @override
    def velocity(self, axis):
        return self.get_speed()

    @override
    def stop(self, axis):
        pyximc.lib.command_stop(self._deviceId)

    @override
    def deinitialize(self, axis):
        raise StandaStageException('Deinitialize command is not supported.')


def search_devices():
    ximc_dir = '/home/labot/Downloads/ximc-2.13.6/ximc/'
    result = pyximc.lib.set_bindy_key(os.path.join(ximc_dir, "win32", "keyfile.sqlite").encode("utf-8"))
    if result != pyximc.Result.Ok:
        pyximc.lib.set_bindy_key("keyfile.sqlite".encode("utf-8")) # Search for the key file in the current directory.

    # This is device search and enumeration with probing. It gives more information about devices.
    probe_flags = pyximc.EnumerateFlags.ENUMERATE_PROBE + pyximc.EnumerateFlags.ENUMERATE_NETWORK
    enum_hints = b"addr="
    # enum_hints = b"addr=" # Use this hint string for broadcast enumerate
    devenum = pyximc.lib.enumerate_devices(probe_flags, enum_hints)
    print("Device enum handle: " + repr(devenum))
    print("Device enum handle type: " + repr(type(devenum)))
    
    dev_count = pyximc.lib.get_device_count(devenum)
    print("Device count: " + repr(dev_count))

    controller_name = pyximc.controller_name_t()
    enum_name_list = []
    for dev_ind in range(0, dev_count):
        enum_name = pyximc.lib.get_device_name(devenum, dev_ind)
        result = pyximc.lib.get_enumerate_device_controller_name(devenum, dev_ind,
                                                                 pyximc.byref(controller_name))
        if result == pyximc.Result.Ok:
            print("Enumerated device #{} name (port name): ".format(dev_ind) + repr(enum_name) + ". Friendly name: " + repr(controller_name.ControllerName) + ".")
            enum_name_list.append(enum_name)

    dict = {'xaxis' : b'xi-com:///dev/ximc/000081B5',
            'yaxis' : b'xi-com:///dev/ximc/000081A1',
            'zaxis' : b'xi-com:///dev/ximc/00008230',
            'tip' : b'xi-com:///dev/ximc/000081A8',
            'tilt' : b'xi-com:///dev/ximc/0000818D'
            }
    return enum_name_list, dict
