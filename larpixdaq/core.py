from __future__ import absolute_import
from __future__ import print_function
from moddaq import Core
import os
import argparse

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

core.run()
