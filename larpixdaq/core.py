from __future__ import absolute_import
from __future__ import print_function
from xylem import Core, EventHandler
import os
import argparse
import requests

parser = argparse.ArgumentParser()
parser.add_argument('--address', default='tcp://127.0.0.1',
        help='base address for ZMQ connections')
parser.add_argument('--log-address', default='tcp://127.0.0.1:5678',
        help='Address to connect to global log')

args = parser.parse_args()
base_address = args.address + ':'

core = Core(base_address + '5551', args.log_address)

allowed_states = ['READY', 'RUN', 'STOP']
core.state = 'STOP'
core.isStateAllowed = lambda x: x in allowed_states

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
announce = EventHandler.EventHandler('new_component', announce_new_client)
announce_lost = EventHandler.EventHandler('lost_component',
        announce_lost_client)
announce_state = EventHandler.EventHandler('state_change',
        announce_state_change)
core.addHandler(announce)
core.addHandler(announce_lost)
core.addHandler(announce_state)

try:
    core.run()
except KeyboardInterrupt:
    pass
