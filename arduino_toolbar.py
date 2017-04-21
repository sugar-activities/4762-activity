#! /usr/bin/env python
# -*- coding: utf-8 -*-

import gtk
import gobject
from random import randint

from gettext import gettext as _

from config import MAX_LOG_ENTRIES

from sugar.graphics.toolbutton import ToolButton
from sugar.graphics.combobox import ComboBox
from sugar.graphics.toolcombobox import ToolComboBox
from sugar.graphics.menuitem import MenuItem
from sugar.graphics.radiotoolbutton import RadioToolButton
from threading import Timer
import logging
import logging.config
from arduino import Arduino

log = logging.getLogger('measure-activity')
log.setLevel(logging.DEBUG)

file_name = 'measure.log'
handler = logging.handlers.RotatingFileHandler(file_name, backupCount=0)
log.addHandler(handler)

LOG_TIMER_VALUES = [1, 10, 300, 3000, 18000]  # In 10th second intervals
LOG_TIMER_LABELS = {1: _('1/10 second'), 10: _('1 second'),
                    300: _('30 seconds'), 3000: _('5 minutes'),
                    30000: _('30 minutes')}

class ArduinoToolbar(gtk.Toolbar):
    ''' The toolbar for specifiying the sensor: temp, distance,
    light or gray '''

    def __init__(self, activity, channels):

        self._arduino_context_id = None

        gtk.Toolbar.__init__(self)
        self.activity = activity
        self._channels = channels

        self.mode = 'arduino'

        # Set up Sensores Button
        self.time = RadioToolButton(group=None)

        self.lista_sensores_button = []

        self.we_are_logging = False
        self._log_this_sample = False
        self._logging_timer = None
        self._logging_counter = 0
        self._image_counter = 0
        self._logging_interval = 0
        self._channels_logged = []
        self._busy = False
        self._take_screenshot = True

        log.debug('se agrega el boton refrescar')
        self.refrescar_button = RadioToolButton(group=None)
        self.refrescar_button.set_named_icon('recargar')
        self.refrescar_button.connect('clicked', self.click_refresh_button)
        self.insert(self.refrescar_button, -1)

        separator = gtk.SeparatorToolItem()
        separator.props.draw = True
        self.insert(separator, -1)

        self.robot = Arduino()

        self._port_entry = gtk.Entry()
        self._port_entry.set_text('A5')  # A
        self._port_entry_changed_id = self._port_entry.connect(
            'changed', self._read_sensor)
        if hasattr(self._port_entry, 'set_tooltip_text'):
            self._port_entry.set_tooltip_text(
                _('Enter a port to read.'))
        self._port_entry.set_width_chars(2)
        self._port_entry.show()
        toolitem = gtk.ToolItem()
        toolitem.add(self._port_entry)
        self.insert(toolitem, -1)
        toolitem.show()

        separator = gtk.SeparatorToolItem()
        separator.props.draw = True
        self.insert(separator, -1)

        self._log_value = LOG_TIMER_VALUES[1]
        self.log_label = gtk.Label(self._log_to_string(self._log_value))
        toolitem = gtk.ToolItem()
        toolitem.add(self.log_label)
        self.insert(toolitem, -1)

        self._log_button = ToolButton('timer-10')
        self._log_button.set_tooltip(_('Select logging interval'))
        self._log_button.connect('clicked', self._log_selection_cb)
        self.insert(self._log_button, -1)
        self._setup_log_palette()


        # Set up Logging/Stop Logging Button
        self._record = ToolButton('media-record')
        self.insert(self._record, -1)
        self._record.set_tooltip(_('Start Recording'))
        self._record.connect('clicked', self.record_control_cb)

        self.show_all()

    def get_log(self):
        return self._log_value

    def get_log_idx(self):
        if self._log_value in LOG_TIMER_VALUES:
            return LOG_TIMER_VALUES.index(self._log_value)
        else:
            return LOG_TIMER_VALUES[0]

    def set_log_idx(self, idx):
        self._log_value = LOG_TIMER_VALUES[idx]
        self.log_label.set_text(self._log_to_string(self._log_value))
        if hasattr(self, '_log_button'):
            self._log_button.set_icon('timer-%d' % (self._log_value))

    def _log_selection_cb(self, widget):
        if self._log_palette:
            if not self._log_palette.is_up():
                self._log_palette.popup(immediate=True,
                                    state=self._log_palette.SECONDARY)
            else:
                self._log_palette.popdown(immediate=True)
            return

    def _log_to_seconds(self, tenth_seconds):
        return tenth_seconds / 10.

    def _log_to_string(self, tenth_seconds):
        if tenth_seconds in LOG_TIMER_LABELS:
            return LOG_TIMER_LABELS[tenth_seconds]
        else:
            return _('1 second')

    def _setup_log_palette(self):
        self._log_palette = self._log_button.get_palette()

        for tenth_seconds in LOG_TIMER_VALUES:
            text = self._log_to_string(tenth_seconds)
            menu_item = MenuItem(icon_name='timer-%d' % (tenth_seconds),
                                 text_label=self._log_to_string(tenth_seconds))
            menu_item.connect('activate', self._log_selected_cb, tenth_seconds)
            self._log_palette.menu.append(menu_item)
            menu_item.show()

    def _log_selected_cb(self, button, seconds):
        self.set_log_idx(LOG_TIMER_VALUES.index(seconds))

    def get_port(self):
        return self._port_value

    def get_port_idx(self):
        if self._port_value in PORT_VALUES:
            return PORT_VALUES.index(self._port_value)
        else:
            return PORT_VALUES[0]

    def set_port_idx(self, idx):
        self._port_value = PORT_VALUES[idx]
        self.port_label.set_text(self._port_to_string(self._port_value))
        if hasattr(self, '_port_button'):
            self._port_button.set_icon('arduino-tools')

    def _port_selection_cb(self, widget):
        if self._port_palette:
            if not self._port_palette.is_up():
                self._port_palette.popup(immediate=True,
                                    state=self._port_palette.SECONDARY)
            else:
                self._port_palette.popdown(immediate=True)
            return

    def _port_to_string(self, tenth_seconds):
        if tenth_seconds in PORT_LABELS:
            return PORT_LABELS[tenth_seconds]
        else:
            return _('1 second')

    def _setup_port_palette(self):
        self._port_palette = self._port_button.get_palette()

        for tenth_seconds in PORT_VALUES:
            text = self._port_to_string(tenth_seconds)
            menu_item = MenuItem(icon_name='arduino-tools',
                                 text_label=self._port_to_string(tenth_seconds))
            menu_item.connect('activate', self._port_selected_cb, tenth_seconds)
            self._port_palette.menu.append(menu_item)
            menu_item.show()

    def _port_selected_cb(self, button, seconds):
        self.set_port_idx(PORT_VALUES.index(seconds))


    def read_sensor_from_bobot_server(self):
        log.debug('**********Read Sensor ***********')
        return 0

    def click_refresh_button(self, event=None):
        log.debug('********** clickea botton refresh ***********')
        self.robot.refresh()
        self.mode = 'reading'
        self.read_sensor_from_bobot_server = self._read_sensor
        self.activity.limpiar_canales()
        self.set_arduino_context()
        return False

    def _port_entry_cb(self, event=None):
        log.debug('********** port_changed ***********')
        self.robot.refresh()
        self.mode = 'reading'
        self.read_sensor_from_bobot_server = self._read_sensor
        self.activity.limpiar_canales()
        self.set_arduino_context()
        return False

    def set_arduino_context(self):
        self.activity.audiograb.stop_grabbing()
        if self._arduino_context_id:
            gobject.source_remove(self._arduino_context_id)
        self._arduino_context_id =\
            gobject.timeout_add(50,self.arduino_context_on)

    def arduino_context_on(self):
        bufChannelTmp = []

        #Si esta el boton de pause activada no se agregar el nuevo valor
        if self.activity.audiograb.get_freeze_the_display():
            bufChannelTmp.append(self.read_sensor_from_bobot_server())
            for i in range(self.activity.audiograb.channels):
                self.activity.wave.new_buffer(bufChannelTmp,i)
                if self.we_are_logging:
                    self.logging_to_file(bufChannelTmp,i)

        #if self.activity.CONTEXT == 'arduino':
        return True
        #else:
        #return False

    def logging_to_file(self, data_buffer, channel):
        if self.we_are_logging:
            if self._logging_counter == MAX_LOG_ENTRIES:
                self._logging_counter = 0
                self.we_are_logging = False
                self.activity.data_logger.stop_session()
            else:
                if self._logging_interval == 0:
                    self._emit_for_logging(data_buffer, channel=channel)
                    self._log_this_sample = False
                    self.we_are_logging = False
                    self.activity.data_logger.stop_session()
                elif self._log_this_sample:
                    # Sample channels in order
                    if self.activity.audiograb._channels_logged.index(False) == channel:
                        self.activity.audiograb._channels_logged[channel] = True
                        self._emit_for_logging(data_buffer, channel=channel)
                        # Have we logged every channel?
                        if self.activity.audiograb._channels_logged.count(True) == self.activity.audiograb.channels:
                            self._log_this_sample = False
                            for i in range(self.activity.audiograb.channels):
                                self.activity.audiograb._channels_logged[i] = False
                            self._logging_counter += 1

    def _emit_for_logging(self, data_buffer, channel=0):
        '''Sends the data for logging'''
        if not self._busy:
            self._busy = True
            if self._take_screenshot:
                if self.activity.data_logger.take_screenshot(
                    self._image_counter):
                    self._image_counter += 1
                else:
                    log.debug('failed to take screenshot %d' % (
                            self._logging_counter))
                self._busy = False
                return

            value_string = data_buffer[0]

            if self.activity.audiograb.channels > 1:
                self.activity.data_logger.write_value(
                    value_string, channel=channel,
                    sample=self._logging_counter)
            else:
                self.activity.data_logger.write_value(
                    value_string, sample=self._logging_counter)
            self._busy = False
        else:
            log.debug('skipping sample %d.%d' % (
                    self._logging_counter, channel))

    def _sample_now(self):
        ''' Log the current sample now. This method is called from the
        _logging_timer object when the interval expires. '''
        self._log_this_sample = True
        self._make_timer()

    def _make_timer(self):
        ''' Create the next timer that will trigger data logging. '''
        self._logging_timer = Timer(self._logging_interval, self._sample_now)
        self._logging_timer.start()

    def record_control_cb(self, button=None):
        ''' Depending upon the selected interval, does either a logging
        session, or just logs the current buffer. '''
        if self.we_are_logging:
            self.set_logging_params(start_stop=False)
            self._record.set_icon('media-record')
            self._record.show()
            self._record.set_tooltip(_('Start Recording'))
        else:
            Xscale = 0.0
            Yscale = 0.0
            interval = self.interval_convert()
            username = self.activity.nick
            if self.activity.wave.get_fft_mode():
                self.activity.data_logger.start_new_session(
                    username, Xscale, Yscale, _(self.logging_interval_status),
                    channels=self._channels, mode='frequency')
            else:
                self.activity.data_logger.start_new_session(
                    username, Xscale, Yscale, _(self.logging_interval_status),
                    channels=self._channels, mode=self.mode)
            self.set_logging_params(
                start_stop=True, interval=interval, screenshot=False)
            self._record.set_icon('record-stop')
            self._record.show()
            self._record.set_tooltip(_('Stop Recording'))
            self.activity.new_recording = True

    def set_logging_params(self, start_stop=False, interval=0,
                           screenshot=True):
        ''' Configures for logging of data: starts or stops a session;
        sets the logging interval; and flags if screenshot is taken. '''
        self.we_are_logging = start_stop
        self._logging_interval = interval
        if not start_stop:
            if self._logging_timer:
                self._logging_timer.cancel()
                self._logging_timer = None
                self._log_this_sample = False
                self._logging_counter = 0
        elif interval != 0:
            self._make_timer()
        self._take_screenshot = screenshot
        self._busy = False

    def interval_convert(self):
        ''' Converts interval string to an integer that denotes the
        number of times the audiograb buffer must be called before a
        value is written.  When set to 0, the whole of current buffer
        will be written. '''
        interval_dictionary = {'1/10 second': 0.1, '1 second': 1,
                               '30 seconds': 30,
                               '5 minutes': 300, '30 minutes': 1800}
        try:
            return interval_dictionary[self.logging_interval_status]
        except ValueError:
            logging.error('logging interval status = %s' %\
                              (str(self.logging_interval_status)))
            return 0

    def take_screenshot(self):
        ''' Capture the current screen to the Journal '''
        log.debug('taking a screenshot %d' % (self._logging_counter))
        self.set_logging_params(start_stop=True, interval=0, screenshot=True)

    def _read_sensor(self, event=None):
        port = self._port_entry.get_text()
        if port.count('A'):
            log.debug( 'analogRead')
            value = self.robot.analogRead(port.strip('A'))
        else:
            log.debug('digitalRead')
            self.robot.pinMode(port, _('INPUT'))
            value = self.robot.digitalRead(port)
        log.debug('VALOR A DEVOLVER')
        value *= 1000
        log.debug(value)
        gtk.gdk.flush()

        return value
