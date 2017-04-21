#!/usr/bin/env python
# Copyright (c) 2012, Alan Aguiar <alanjas@hotmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import os
import sys
import commands

from gettext import gettext as _
sys.path.insert(0, os.path.abspath('./plugins/arduino'))
import pyfirmata

VALUE = {_('HIGH'): 1, _('LOW'): 0}
MODE = {_('INPUT'): pyfirmata.INPUT, _('OUTPUT'): pyfirmata.OUTPUT,
        _('PWM'): pyfirmata.PWM, _('SERVO'): pyfirmata.SERVO}

ERROR = _('ERROR: Check the Arduino and the number of port.')
ERROR_VALUE_A = _('ERROR: Value must be a number from 0 to 1.')
ERROR_VALUE_S = _('ERROR: Value must be a number from 0 to 180.')
ERROR_VALUE_D = _('ERROR: Value must be either HIGH or LOW, 0 or 1')
ERROR_MODE = _('ERROR: The mode must be either INPUT, OUTPUT, PWM or SERVO.')
ERROR_VALUE_TYPE = _('ERROR: The value must be an integer.')
ERROR_PIN_TYPE = _('ERROR: The pin must be an integer.')
ERROR_PIN_CONFIGURED = _('ERROR: You must configure the mode for the pin.')

COLOR_NOTPRESENT = ["#A0A0A0","#808080"]
COLOR_PRESENT = ["#00FFFF","#00A0A0"]


class Arduino():
    def __init__(self):
        self._baud = 57600
        self.active_arduino = 0
        self._arduinos = []
        self._arduinos_it = []
        
    def pinMode(self, pin, mode):
        self._check_init()
        try:
            pin = int(pin)
        except:
            print 'The pin must be an integer'
        if (mode in MODE):
            try:
                a = self._arduinos[self.active_arduino]
                a.digital[pin]._set_mode(MODE[mode])
            except:
                print ERROR
        else:
            print ERROR_MODE

    def analogRead(self, pin):
        try:
            pin = int(pin)
        except:
            print ERROR_PIN_TYPE
        res = '30'
        #try:
        print self._arduinos
        a = self._arduinos[self.active_arduino]
        a.analog[pin].enable_reporting()
        a.pass_time(0.05) # wait for the iterator to start receiving data
        res = a.analog[pin].read()
        a.digital[pin].disable_reporting()
        #except:
            #pass
        return res

    def digitalRead(self, pin):
        try:
            pin = int(pin)
        except:
            print ERROR_PIN_TYPE
        try:
            a = self._arduinos[self.active_arduino]
            mode = a.digital[pin]._get_mode()
        except:
            print ERROR
        if mode != MODE[_('INPUT')]:
            print ERROR_PIN_CONFIGURED
        res = -1
        try:
            a = self._arduinos[self.active_arduino]
            a.digital[pin].enable_reporting()
            a.pass_time(0.05) # wait for the iterator to start receiving data
            if a.digital[pin].read() is None:
                # if the library returns None it is actually False  not being updated
                res = False
            else:
                res = a.digital[pin].read()
            a.digital[pin].disable_reporting()
        except:
            pass
        return res

    def _check_init(self):
        n = len(self._arduinos)
        if (self.active_arduino > n) or (self.active_arduino < 0):
            print 'Not found Arduino '

    def refresh(self):
        #Close actual Arduinos
        for dev in self._arduinos:
            try:
                dev.exit()
            except:
                pass
        self._arduinos = []
        self._arduinos_it = []
        #Search for new Arduinos
        status,output_usb = commands.getstatusoutput("ls /dev/ | grep ttyUSB")
        output_usb_parsed = output_usb.split('\n')
        status,output_acm = commands.getstatusoutput("ls /dev/ | grep ttyACM")
        output_acm_parsed = output_acm.split('\n')
        output = output_usb_parsed
        output.extend(output_acm_parsed)
        for dev in output:
            if not(dev == ''):
                n = '/dev/%s' % dev
                #try:
                board = pyfirmata.Arduino(n, baudrate=self._baud)
                #board = Arduino /dev/ttyACM0
                it = pyfirmata.util.Iterator(board)
                it.start()
                self._arduinos.append(board)
                self._arduinos_it.append(it)
                print '***MORE APPEND'
                print board
                #except Exception, err:
                    #print err
                    #print 'Error loading board'
