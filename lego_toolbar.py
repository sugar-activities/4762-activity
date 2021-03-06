#! /usr/bin/env python
# -*- coding: utf-8 -*-

import gtk
import gobject
import random

from gettext import gettext as _

from config import MAX_LOG_ENTRIES

from NxtSensorPlugin import NxtSensorPlugin

from sugar.graphics.toolbutton import ToolButton
from sugar.graphics.combobox import ComboBox
from sugar.graphics.menuitem import MenuItem
from sugar.graphics.toolcombobox import ToolComboBox
from sugar.graphics.radiotoolbutton import RadioToolButton
from threading import Timer
import logging
import logging.config

log = logging.getLogger('measure-activity')
log.setLevel(logging.DEBUG)

file_name = 'measure.log'
handler = logging.handlers.RotatingFileHandler(file_name, backupCount=0)
nxt = NxtSensorPlugin()

LOG_TIMER_VALUES = [1, 10, 300, 3000, 18000]  # In 10th second intervals
LOG_TIMER_LABELS = {1: _('1/10 second'), 10: _('1 second'),
                    300: _('30 seconds'), 3000: _('5 minutes'),
                    30000: _('30 minutes')}

PORT_VALUES = [1, 2, 3, 4]  # In 10th second intervals
PORT_LABELS = {1: _('Port 1'), 2: _('Port 2'), 3: _('Port 3'), 4: _('Port 4')}


class LegoToolbar(gtk.Toolbar):
    ''' The toolbar for specifiying the sensor: temp, distance,
    light or gray '''

    def __init__(self, activity, channels):

        #Its used to avoid it from running twice
        self._lego_context_id = None

        gtk.Toolbar.__init__(self)
        self.activity = activity
        self._channels = channels

        self.mode = 'lego'

        # Set up Sensores Button
        self.time = RadioToolButton(group=None)

        # Keeps the button list (sensors)
        # added to the LegoToolbar
        self.lista_sensores_button = []

        self.we_are_logging = False
        self._log_this_sample = False
        self._logging_timer = None
        self._logging_counter = 0
        self._image_counter = 0
        self._logging_interval = 0
        self._port_status = 1
        self._channels_logged = []
        self._busy = False
        self._take_screenshot = True

        self.refrescar_button = RadioToolButton(group=None)
        self.refrescar_button.set_named_icon('recargar')
        self.insert(self.refrescar_button, -1)

        separator = gtk.SeparatorToolItem()
        separator.props.draw = True
        self.insert(separator, -1)

        self.load_buttons()

        separator = gtk.SeparatorToolItem()
        separator.props.draw = True
        self.insert(separator, -1)

        self._port = PORT_VALUES[0]
        self.port_label = gtk.Label(self._port_to_string(self._port))
        toolitem = gtk.ToolItem()
        toolitem.add(self.port_label)
        self.insert(toolitem, -1)

        self._port_button = ToolButton('LEGO-tools')
        self._port_button.set_tooltip(_('Select Port'))
        self._port_button.connect('clicked', self._port_selection_cb)
        self.insert(self._port_button, -1)
        self._setup_port_palette()


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
            self._port_button.set_icon('LEGO-tools')

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
            menu_item = MenuItem(icon_name='LEGO-tools',
                                 text_label=self._port_to_string(tenth_seconds))
            menu_item.connect('activate', self._port_selected_cb, tenth_seconds)
            self._port_palette.menu.append(menu_item)
            menu_item.show()

    def _port_selected_cb(self, button, seconds):
        self.set_port_idx(PORT_VALUES.index(seconds))

    #LEGO set up the sensor buttons
    def load_buttons(self):
        self.sensores = [_('Light Sensor'), _('Distance Sensor'), _('Grey Sensor'), _('Button Sensor'), _('Sound Sensor')]
        self.lista_sensores_button = []
        for i in range(len(self.sensores)):
            self.sensor = self.sensores[i]
            radio_tool_button = RadioToolButton(group=self.time)
            icono = self.sensor.strip('0123456789:')
            radio_tool_button.set_named_icon(icono)
            radio_tool_button.set_tooltip(_(self.sensor))
            if self.sensor.count(_('Sound Sensor')):
                radio_tool_button.connect('clicked',self.click_sound_button)
            if self.sensor.count(_('Distance Sensor')):
                radio_tool_button.connect('clicked',self.click_dist_button)
            elif self.sensor.count(_('Grey Sensor')):
                radio_tool_button.connect('clicked',self.click_grises_button)
            elif self.sensor.count(_('Button Sensor')):
                radio_tool_button.connect('clicked',self.click_button)
                log.debug(self.sensores)
            elif self.sensor.count(_('Light sensor')):
                radio_tool_button.connect('clicked',self.click_luz_button)
            self.insert(radio_tool_button, 2)
            self.lista_sensores_button.append(radio_tool_button)


    def get_sensor_number(self):
        log.debug('GETING SENSOR NUMBER')
        log.debug(str(self._port_status))
        return self._port_status

    # LEGO reading sensor functions
    def read_sound_from_bobot_server(self):
        return nxt.getSound(self.get_port())

    def read_dist_from_bobot_server(self):
        return nxt.getDistance(self.get_port())

    def read_boton_from_bobot_server(self):
        return nxt.getButton(self.get_port())

    def read_grises_from_bobot_server(self):
        return nxt.getGray(self.get_port())

    def read_luz_from_bobot_server(self):
        return nxt.getLight(self.get_port())

    def read_sensor_from_bobot_server(self):
        return 0

    def click_button(self,button=None):
        self.set_lego_context()
        return False

    def click_sound_button(self, button=None):
        self.mode = 'temperatura'
        self.read_sensor_from_bobot_server = self.read_sound_from_bobot_server
        self.set_lego_context()
        return False

    def click_dist_button(self, button=None):
        self.mode = 'distancia'
        self.read_sensor_from_bobot_server = self.read_dist_from_bobot_server
        self.activity.limpiar_canales()
        self.set_lego_context()
        return False

    def click_boton_button(self, button=None):
        self.mode = 'boton'
        self.read_sensor_from_bobot_server = self.read_boton_from_bobot_server
        self.activity.limpiar_canales()
        self.set_lego_context()
        return False

    def click_grises_button(self, button=None):
        self.mode = 'grises'
        self.read_sensor_from_bobot_server = self.read_grises_from_bobot_server
        self.activity.limpiar_canales()
        self.set_lego_context()
        return False

    def click_luz_button(self, button=None):
        self.mode = 'luz'
        self.read_sensor_from_bobot_server = self.read_luz_from_bobot_server
        self.activity.limpiar_canales()
        self.set_lego_context()
        return False

    def set_lego_context(self):
        self.activity.audiograb.stop_grabbing()
        if self._lego_context_id:
            gobject.source_remove(self._lego_context_id)
        self._lego_context_id =\
            gobject.timeout_add(50,self.lego_context_on)

    def lego_context_on(self):
        bufChannelTmp = []

        #If pause button is active, do not add the value
        if self.activity.audiograb.get_freeze_the_display():
            bufChannelTmp.append(self.read_sensor_from_bobot_server())
            for i in range(self.activity.audiograb.channels):
                self.activity.wave.new_buffer(bufChannelTmp,i)
                if self.we_are_logging:
                    self.logging_to_file(bufChannelTmp,i)

        if self.activity.CONTEXT == 'lego':
            return True
        else:
            return False

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
                    if self.activity.audiograb._channels_logged.index(False) ==\
                            channel:
                        self.activity.audiograb._channels_logged[channel] =\
                            True
                        self._emit_for_logging(data_buffer, channel=channel)
                        # Have we logged every channel?
                        if self.activity.audiograb._channels_logged.count(True)\
                                == self.activity.audiograb.channels:
                            self._log_this_sample = False
                            for i in range(self.activity.audiograb.channels):
                                self.activity.audiograb._channels_logged[i] =\
                                    False
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
            self.activity.audiograb.set_logging_params(start_stop=False)
            self._record.set_icon('media-record')
            self._record.show()
            self._record.set_tooltip(_('Start Recording'))
        else:
            Xscale = (1.00 / self.activity.audiograb.get_sampling_rate())
            Yscale = 0.0
            interval = self._log_value / 10. # self.interval_convert()
            username = self.activity.nick
            if self.activity.wave.get_fft_mode():
                self.activity.data_logger.start_new_session(
                    username, Xscale, Yscale,
                    self._log_to_string(self._log_value),
                    channels=self._channels, mode='frequency')
            else:
                self.activity.data_logger.start_new_session(
                    username, Xscale, Yscale,
                    self._log_to_string(self._log_value),
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
