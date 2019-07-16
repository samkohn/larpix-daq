from __future__ import absolute_import
from __future__ import print_function
from xylem import Core
from xylem.EventHandler import EventHandler
import os
import argparse
import requests

class LArPixCore(object):
    """The core is responsible for managing and monitoring the DAQ
    system components. This includes tracking which components are
    connected, broadcasting the DAQ state, and sending operator commands
    to different components.

    The core must be the first script launched, since other components
    will exit if they cannot connect to the core.

    Operator/user interaction with the DAQ Core, and therefore the
    rest of the DAQ system, happens exclusively through the LArPix DAQ
    Operator module. See the :py:class:`Operator documentation
    <.Operator>` for available commands.

    """
    def __init__(self, address, log_address):
        self.core = Core(address, log_address)
        self._allowed_states = ['READY', 'RUN', 'STOP']
        self.core.state = 'STOP'
        self.core.isStateAllowed = lambda x: x in self._allowed_states
        server = 'http://localhost:5000/'

        def announce_new_client(client_name, all_client_names):
            try:
                r = requests.post(server + '/component',
                        json={'new':client_name, 'all':all_client_names})
            except:
                pass
        def announce_lost_client(client_name, all_client_names):
            try:
                r = requests.delete(server + '/component',
                        json={'lost':client_name, 'all':all_client_names})
            except:
                pass
        def announce_state_change(new_state, old_state):
            try:
                r = requests.post(server + '/state', json={'new':
                    new_state, 'old': old_state})
            except:
                pass
        announce = EventHandler('new_component', announce_new_client)
        announce_lost = EventHandler('lost_component', announce_lost_client)
        announce_state = EventHandler('state_change', announce_state_change)
        self.core.addHandler(announce)
        self.core.addHandler(announce_lost)
        self.core.addHandler(announce_state)

    def run(self):
        """Enter the event loop for the Core."""
        self.core.run()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--address', default='tcp://127.0.0.1',
            help='base address for ZMQ connections')
    parser.add_argument('--log-address', default='tcp://127.0.0.1:5678',
            help='Address to connect to global log')

    args = parser.parse_args()
    base_address = args.address + ':'

    core = LArPixCore(base_address + '5551', args.log_address)

    try:
        core.run()
    except KeyboardInterrupt:
        pass
