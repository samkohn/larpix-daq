from __future__ import absolute_import
from __future__ import print_function
from moddaq import Core
import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--address', default='tcp://127.0.0.1',
        help='base address for ZMQ connections')

args = parser.parse_args()
base_address = args.address + ':'

core = Core(base_address + '5550', base_address + '5551')

allowed_states = ['', 'START', 'INIT', 'READY', 'RUN',
        'SUBROUTINE', 'STOP']
core.isStateAllowed = lambda x: x in allowed_states
core.state = 'START'

core.run()
