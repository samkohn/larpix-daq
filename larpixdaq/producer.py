from __future__ import absolute_import
from __future__ import print_function
import argparse
import logging
import time
import ast
import json
from moddaq import Producer
import larpix.quickstart as larpix_quickstart
from larpix.fakeio import FakeIO
from larpix.zmq_io import ZMQ_IO
import larpix.larpix as larpix

from larpixdaq.packetformat import toBytes

try:
    parser = argparse.ArgumentParser()
    parser.add_argument('address')
    parser.add_argument('--core', default='tcp://127.0.0.1')
    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('--fake', action='store_true')
    args = parser.parse_args()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    address = args.address
    core_url = args.core
    core_address = core_url + ':5550'
    response_address = core_url + ':5551'
    kwargs = {
            'core_address': core_address,
            'response_address': response_address,
            'heartbeat_time_ms': 300,
            'action_docs': {
                'configure_chip': '''configure_chip(chipid, name, value,
                    channel='')
                    Update the configuration stored in software.''',
                'bulk_configure': '''bulk_configure(configuration_json)
                    Update the configuration stored in software.''',
                'configure_name': '''configure_name(name, chipid,
                    iochain)
                    Load the named configuration into software.''',
                'write_config': '''write_config(chipid, registers='',
                    write_read='', message='')
                    Send the configuration from software to the board.''',
                'read_config': '''read_config(chipid, registers='',
                    message='')
                    Read the configuration from the board.''',
                'validate_config': '''validate_config(chipid)
                    Read the given chip's configuration and compare it
                    to the configuration stored in software. Returns
                    True or False.''',
                'learn_config': '''learn_config(chipid)
                    Read the given chip's configuration and use it to
                    overwrite the configuration stored in software.''',
                'fetch_configs': '''fetch_configs()
                    Return a list of available configurations.''',
                'retrieve_config': '''retrieve_config(chipid)
                    Return a dict representation of the given chip's
                    configuration that is stored in software.''',
                'send_config': '''send_config(updates)
                    Apply the given updates to the software
                    configuration.''',
                'quickstart': '''quickstart(board_name='pcb-1')
                    Start up the board into a quiescent state.''',
                'list_routines': '''list_routines()
                    Return a list of available routines and their call
                    signatures.''',
                'run_routine': '''run_routine(name, *args)
                    Run the specified routine with the specified
                    arguments. Call ``list_routines`` to learn the
                    argument lists for each available routine.''',
                'sleep': '''sleep(time_in_sec)
                    Wait a certain amount of time and then reply with
                    'success'.''',
            },
    }
    producer = Producer(address, name='LArPix board', group='BOARD', **kwargs)
    board = larpix.Controller()
    if args.fake:
        board.io = FakeIO()
    else:
        board.io = ZMQ_IO('tcp://10.0.1.6')
    board.use_all_chips = True
    state = ''
    run = False
    configurations = {
            'startup': 'startup.json',
            'quiet': 'quiet.json',
    }
    routines = {
            'quickstart': 'quickstart()',
            'leakage_current_scan': 'leakage_current_scan(chips)',
    }
    def configure_chip(chipid_str, name_str, value_str, channel_str=''):
        '''
        Update the chip configuration stored in software.

        '''
        try:
            global board
            chipid = int(chipid_str)
            value = int(value_str)
            channel = int(channel_str) if channel_str else None
            chip = board.get_chip(chipid, 0)
            if channel is None:
                setattr(chip.config, name_str, value)
            else:
                getattr(chip.config, name_str)[channel] = value
            logging.debug('updated configuration')
            logging.debug(chip)
            logging.debug(getattr(chip.config, name_str))
            return 'success'
        except Exception as e:
            logging.exception(e)
            return 'ERROR: %s' % e
    def bulk_config(configuration_json):
        '''
        Update the configuration stored in software.

        '''
        try:
            global board
            bulk_config = json.loads(configuration_json)
            for chipid, iochain in bulk_config:
                chip = board.get_chip(chipid, iochain)
                chip.config.from_dict(bulk_config[chipid, iochain])
            return 'success'
        except Exception as e:
            logging.exception(e)
            return 'ERROR: %s' % e
    def configure_name(name, chipid, iochain):
        '''
        Load the named configuration into software.

        '''
        try:
            global board
            chip = board.get_chip(chipid, iochain)
            chip.config.load(configurations[name])
            return 'success'
        except Exception as e:
            logging.exception(e)
            return 'ERROR: %s' % e
    def write_config(chipid_str, registers_str='', write_read_str='',
            message=''):
        '''
        Send the given configuration to the board.

        '''
        try:
            global board
            chipid = int(chipid_str)
            chip = board.get_chip(chipid, 0)
            if registers_str:  # treat as int or list
                registers = ast.literal_eval(registers_str)
            else:
                registers = None
            if not write_read_str:
                write_read = 0
            if not message:
                message = None
            board.write_configuration(chip, registers, write_read,
                    message)
            return 'success'
        except Exception as e:
            logging.exception(e)
            return 'ERROR: %s' % e

    def read_config(chipid_str, registers_str='', message=''):
        '''
        Read configurations from the board.

        '''
        try:
            global board
            chipid = int(chipid_str)
            chip = board.get_chip(chipid, 0)
            if registers_str:  # treat as int or list
                registers = ast.literal_eval(registers_str)
            else:
                registers = None
            if not message:
                message = None
            board.read_configuration(chip, registers, message=message)
            packets = board.reads[-1]
            result = '\n'.join(str(p) for p in packets if p.packet_type
                    == p.CONFIG_READ_PACKET)
            return result
        except Exception as e:
            logging.exception(e)
            return 'ERROR: %s' % e
    def validate_config(chipid_str):
        '''
        Read configurations from the board and compare to those stored
        in software, returning True if they're equal.

        '''
        try:
            global board
            chipid = int(chipid_str)
            chip = board.get_chip(chipid, 0)
            if isinstance(board.io, FakeIO):
                packets = chip.get_configuration_packets(
                        larpix.Packet.CONFIG_WRITE_PACKET)
                for p in packets:
                    p.packet_type = larpix.Packet.CONFIG_READ_PACKET
                board.io.queue.append((packets, b'some bytes'))
            result = board.verify_configuration(chip_id=chipid)
            return result
        except Exception as e:
            logging.exception(e)
            return 'ERROR: %s' % e
    def learn_config(chipid_str):
        '''
        Read configurations from the board and use the values to
        overwrite the configuration in software.

        '''
        try:
            global board
            chipid = int(chipid_str)
            chip = board.get_chip(chipid, 0)
            if isinstance(board.io, FakeIO):
                packets = chip.get_configuration_packets(
                        larpix.Packet.CONFIG_WRITE_PACKET)
                board.io.queue.append((packets, b'some bytes'))
            board.read_configuration(chip)
            updates_dict = {}
            for packet in board.reads[-1]:
                if packet.packet_type == packet.CONFIG_READ_PACKET:
                    updates_dict[packet.register_address] = (
                            packet.register_data)
            chip.config.from_dict_registers(updates_dict)
            return 'success'
        except Exception as e:
            logging.exception(e)
            return 'ERROR: %s' % e
    def fetch_configs():
        '''
        Return the ``configurations`` dict's keys.

        '''
        try:
            result = list(configurations.keys())
            return result
        except Exception as e:
            logging.exception(e)
            return 'ERROR: %s' % e
    def retrieve_config(chipid_str):
        '''
        Return the current configuration stored in software for the
        given chip.

        '''
        try:
            global board
            chipid = int(chipid_str)
            chip = board.get_chip(chipid, 0)
            return chip.config.to_dict()
        except Exception as e:
            logging.exception(e)
            return 'ERROR: %s' % e
    def send_config(updates):
        '''
        Apply the given updates to the software configuration.

        '''
        try:
            global board
            for chipid_str, chip_updates in updates.items():
                chip = board.get_chip(int(chipid_str), 0)
                chip.config.from_dict(chip_updates)
            return 'success'
        except Exception as e:
            logging.exception(e)
            return 'ERROR: %s' % e
    def quickstart(board_name='pcb-1'):
        '''
        Start up the board and configure chips to a quiescent state.

        '''
        try:
            global board
            board = larpix_quickstart.quickcontroller(board_name,
                    io=board.io)
            result = 'success'
            return result
        except Exception as e:
            logging.exception(e)
            return 'ERROR: %s' % e
    def list_routines():
        '''
        List the available routines.

        '''
        try:
            return routines
        except Exception as e:
            logging.exception(e)
            return 'ERROR: %s' % e
    def run_routine(name, *args):
        '''
        Run the given routine.

        '''
        try:
            result = routine_calls[name](*args)
            return result
        except Exception as e:
            logging.exception(e)
            return 'ERROR: %s' % e
    def sleep(time_in_sec):
        '''
        Sleep and return success.

        '''
        try:
            delay = int(time_in_sec)
            time.sleep(delay)
            return 'success'
        except Exception as e:
            logging.exception(e)
            return 'ERROR: %s' % e

    routine_calls = {
            'quickstart': quickstart,
            'leakage_current_scan': lambda chips: ('Ran scan on %s' %
                chips),
    }
    producer.actions['configure_chip'] = configure_chip
    producer.actions['write_config'] = write_config
    producer.actions['read_config'] = read_config
    producer.actions['validate_config'] = validate_config
    producer.actions['learn_config'] = learn_config
    producer.actions['quickstart'] = quickstart
    producer.actions['configure_name'] = configure_name
    producer.actions['fetch_configs'] = fetch_configs
    producer.actions['retrieve_config'] = retrieve_config
    producer.actions['send_config'] = send_config
    producer.actions['list_routines'] = list_routines
    producer.actions['run_routine'] = run_routine
    producer.actions['sleep'] = sleep
    producer.request_state()
    while True:
        producer.receive(0.4)
        if state != producer.state:
            print('State update: New state: %s' % producer.state)
            state = producer.state
        if state == 'RUN':
            if not board.io.is_listening:
                logging.debug('about to start listening')
                board.start_listening()
            if isinstance(board.io, FakeIO):
                p = larpix.Packet()
                p.timestamp = int(time.time()) % 100000
                p.assign_parity()
                board.io.queue.append(([p], p.bytes() + b'\x00'))
            data = board.read()
            logging.debug('just took data')
            metadata = {'name': 'LArPix board', 'timestamp':
                    time.time()}
            to_produce = toBytes(data[0])
            logging.debug('producing packets: %s...' %
                    repr(to_produce[:20]))
            producer.produce(metadata, to_produce)
        else:
            if board.io.is_listening:
                board.stop_listening()
finally:
    producer.cleanup()
