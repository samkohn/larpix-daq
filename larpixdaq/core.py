from __future__ import absolute_import
from __future__ import print_function
from moddaq import Core, EventHandler
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

allowed_states = ['', 'START', 'INIT', 'READY', 'RUN',
        'SUBROUTINE', 'STOP']
core.isStateAllowed = lambda x: x in allowed_states
core.state = 'START'

def announce_new_client(client_name, all_client_names):
    print("NEW CLIENT!!!! %s" % client_name)
def announce_lost_client(client_name, all_client_names):
    print("LOST CLIENT!!! remaining: %s" % all_client_names)
def announce_state_change(new_state, old_state):
    r = requests.post('http://localhost:5561/state', data={'new':
        new_state, 'old': old_state})
def new_action(client, action, params):
    print("NEW ACTION FOR %s: %s(%s)" % (client, action, params))
def finished_action(client, action, params, result):
    print("FINISHED ACTION FOR %s: %s(%s) = %s" % (client, action,
        params, result))
announce = EventHandler.EventHandler('new_component', announce_new_client)
announce_lost = EventHandler.EventHandler('lost_component',
        announce_lost_client)
announce_state = EventHandler.EventHandler('state_change',
        announce_state_change)
handle_new_action = EventHandler.EventHandler('action_request',
        new_action)
handle_finished_action = EventHandler.EventHandler('action_complete',
        finished_action)
core.addHandler(announce)
core.addHandler(announce_lost)
core.addHandler(announce_state)
core.addHandler(handle_new_action)
core.addHandler(handle_finished_action)

core.run()
