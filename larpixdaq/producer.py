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
from larpixdaq.routines import Routine, producer_routines


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
    core_address = core_url + ':5551'
    kwargs = {
            'core_address': core_address,
            'heartbeat_time_ms': 300,
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
    def configure_chip(chipid_str, name_str, value_str, channel_str=''):
        '''
        configure_chip(chipid, name, value, channel='')

        Update the configuration stored in software.

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
        bulk_configure(configuration_json)

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
        configure_name(name, chipid, iochain)

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
        write_config(chipid, registers='', write_read='', message='')

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
        read_config(chipid, registers='', message='')

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
            if isinstance(board.io, FakeIO):
                packets = chip.get_configuration_packets(
                        larpix.Packet.CONFIG_WRITE_PACKET)
                for p in packets:
                    p.packet_type = larpix.Packet.CONFIG_READ_PACKET
                    p.assign_parity()
                board.io.queue.append((packets, b'some bytes'))
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
        validate_config(chipid)

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
        learn_config(chipid)

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
        fetch_configs()

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
        retrieve_config(chipid)

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
        send_config(updates)

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
    def list_routines():
        '''
        list_routines()

        List the available routines.

        '''
        try:
            return [{
                'name': name,
                'params': [{'name': p, 'type': 'input'} for p in
                    r.params],
                }
                for name, r in routines.items()
                ]
        except Exception as e:
            logging.exception(e)
            return 'ERROR: %s' % e
    def run_routine(name, *args):
        '''
        run_routine()

        Run the given routine.

        '''
        try:
            global board
            board, result = routines[name].func(board, *args)
            return result
        except Exception as e:
            logging.exception(e)
            return 'ERROR: %s' % e
    def sleep(time_in_sec):
        '''
        sleep()

        Sleep and return success.

        '''
        try:
            delay = int(time_in_sec)
            time.sleep(delay)
            return 'success'
        except Exception as e:
            logging.exception(e)
            return 'ERROR: %s' % e

    ############
    # Routines #
    ############
    def quickstart(board, board_name='pcb-1'):
        '''
        quickstart(board_name='pcb-1')

        Start up the board and configure chips to a quiescent state.

        '''
        board = larpix_quickstart.quickcontroller(board_name,
                io=board.io)
        result = 'success'
        return board, result

    routines = {
            'quickstart': Routine('quickstart', quickstart, ['board']),
            'leakage_current_scan': Routine('leakage_current_scan',
                lambda board, chip: (board, 'Ran scan on %s' % chip),
                ['chip', 'timeout', 'repeats']),
    }
    routines.update(producer_routines)
    producer.register_action('configure_chip', configure_chip,
            configure_chip.__doc__)
    producer.register_action('write_config', write_config,
            write_config.__doc__)
    producer.register_action('read_config', read_config, read_config.__doc__)
    producer.register_action('validate_config', validate_config,
            validate_config.__doc__)
    producer.register_action('learn_config', learn_config,
            learn_config.__doc__)
    producer.register_action('configure_name', configure_name,
            configure_name.__doc__)
    producer.register_action('fetch_configs', fetch_configs,
            fetch_configs.__doc__)
    producer.register_action('retrieve_config', retrieve_config,
            retrieve_config.__doc__)
    producer.register_action('send_config', send_config, send_config.__doc__)
    producer.register_action('list_routines', list_routines,
            list_routines.__doc__)
    producer.register_action('run_routine', run_routine, run_routine.__doc__)
    producer.register_action('sleep', sleep, sleep.__doc__)
    producer.request_state()
    while True:
        producer.receive(0.4)
        if state != producer.state:
            print('State update: New state: %s' % producer.state)
            state = producer.state
            if state == 'RUN':
                producer.send_info('Beginning run')
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
