"""
Copyright 2011 Ryan Fobel

This file is part of dmf_control_board.

dmf_control_board is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

dmf_control_board is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with dmf_control_board.  If not, see <http://www.gnu.org/licenses/>.
"""
from collections import OrderedDict
from datetime import datetime

import gtk
import zmq
from flatland import String, Boolean, Float, Form
from logger import logger
from gui.protocol_grid_controller import ProtocolGridController
from plugin_helpers import (AppDataController, StepOptionsController,
                            get_plugin_info)
from plugin_manager import (IPlugin, IWaveformGenerator, Plugin, implements,
                            PluginGlobals, ScheduleRequest, emit_signal,
                            get_service_instance)
from app_context import get_app
from path_helpers import path


PluginGlobals.push_env('microdrop.managed')

class ZeroMQServicePlugin(Plugin, AppDataController, StepOptionsController):
    """
    This class is automatically registered with the PluginManager.
    """
    implements(IPlugin)
    version = get_plugin_info(path(__file__).parent.parent).version
    plugins_name = get_plugin_info(path(__file__).parent.parent).plugin_name

    '''
    AppFields
    ---------

    A flatland Form specifying application options for the current plugin.
    Note that nested Form objects are not supported.

    Since we subclassed AppDataController, an API is available to access and
    modify these attributes.  This API also provides some nice features
    automatically:
        -all fields listed here will be included in the app options dialog
            (unless properties=dict(show_in_gui=False) is used)
        -the values of these fields will be stored persistently in the microdrop
            config file, in a section named after this plugin's name attribute
    '''
    AppFields = Form.of(
        String.named('service_address').using(default='', optional=True),
    )

    '''
    StepFields
    ---------

    A flatland Form specifying the per step options for the current plugin.
    Note that nested Form objects are not supported.

    Since we subclassed StepOptionsController, an API is available to access and
    modify these attributes.  This API also provides some nice features
    automatically:
        -all fields listed here will be included in the protocol grid view
            (unless properties=dict(show_in_gui=False) is used)
        -the values of these fields will be stored persistently for each step
    '''
    StepFields = Form.of(
        Boolean.named('service_enabled').using(default=False, optional=True),
        Float.named('timeout_sec').using(default=5., optional=True),
    )

    def __init__(self):
        self.name = self.plugins_name
        self.context = zmq.Context.instance()
        self.socks = OrderedDict()
        self.timeout_id = None
        self._start_time = None

    def on_plugin_enable(self):
        # We need to call AppDataController's on_plugin_enable() to update the
        # application options data.
        AppDataController.on_plugin_enable(self)
        self.context = zmq.Context()
        self.reset_socks()
        if get_app().protocol:
            pgc = get_service_instance(ProtocolGridController, env='microdrop')
            pgc.update_grid()

    def close_socks(self):
        # Close any currently open sockets.
        for name, sock in self.socks.iteritems():
            sock.close()
        self.socks = OrderedDict()

    def reset_socks(self):
        self.close_socks()
        app_values = self.get_app_values()
        if self.timeout_id is not None:
            gtk.timeout_remove(self.timeout_id)
            self.timeout_id = None
        if app_values['service_address']:
            # Service address is available
            self.socks['req'] = zmq.Socket(self.context, zmq.REQ)
            self.socks['req'].connect(app_values['service_address'])

    def on_app_options_changed(self, plugin_name):
        if plugin_name == self.name:
            self.reset_socks()

    def on_plugin_disable(self):
        self.close_socks()
        if get_app().protocol:
            pgc = get_service_instance(ProtocolGridController, env='microdrop')
            pgc.update_grid()

    def _on_check_service_response(self, timeout_sec):
        if not self.socks['req'].poll(timeout=11):
            # No response is ready yet.
            if timeout_sec < (datetime.now() -
                              self._start_time).total_seconds():
                # Timed out waiting for response.
                self.reset_socks()
                self.step_complete(return_value='Fail')
                self.timeout_id = None
                return False
            return True
        else:
            # Response is ready.
            response = self.socks['req'].recv()
            logger.info('[ZeroMQServicePlugin] Service response: %s', response)
            if response == 'completed':
                logger.info('[ZeroMQServicePlugin] Service completed task '
                            'successfully.')
                self.step_complete()
            else:
                logger.error('[ZeroMQServicePlugin] Unexpected response: %s' %
                             response)
                self.step_complete(return_value='Fail')
            self.timeout_id = None
            return False

    def step_complete(self, return_value=None):
        app = get_app()
        if app.running or app.realtime_mode:
            emit_signal('on_step_complete', [self.name, return_value])

    def on_step_run(self):
        options = self.get_step_options()
        self.reset_socks()
        if options['service_enabled'] and self.socks['req'] is None:
            # Service is supposed to be called for this step, but the socket is
            # not ready.
            self.step_complete(return_value='Fail')
        elif options['service_enabled'] and self.socks['req'] is not None:
            logger.info('[ZeroMQServicePlugin] Send signal to service to '
                        'start.')
            # Request start of service.
            self.socks['req'].send('start')
            if not self.socks['req'].poll(timeout=4000):
                self.reset_socks()
                logger.error('[ZeroMQServicePlugin] Timed-out waiting for '
                                'a response.')
            else:
                # Response is ready.
                response = self.socks['req'].recv()
                if response == 'started':
                    logger.info('[ZeroMQServicePlugin] Service started '
                                'successfully.')
                    self.socks['req'].send('notify_completion')
                    self._start_time = datetime.now()
                    self.timeout_id = gtk.timeout_add(
                        100, self._on_check_service_response,
                        options['timeout_sec'])
        else:
            self.step_complete()

    def enable_service(self):
        pass

PluginGlobals.pop_env()
