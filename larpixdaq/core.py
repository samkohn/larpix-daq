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
core.address_service.bind_base = base_address
core.address_service.connect_base = base_address
filepath = os.path.join(os.path.dirname(__file__), 'architecture.cfg')
architecture = core.address_service.loadFile(filepath)

allowed_states = ['', 'START', 'INIT', 'READY', 'RUN',
        'CONFIGURATION', 'SUBROUTINE', 'STOP']
core.isStateAllowed = lambda x: x in allowed_states

core.run()
