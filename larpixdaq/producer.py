from __future__ import absolute_import
from __future__ import print_function
import argparse
import logging
import time
import ast
import json
import random

from xylem import Producer
import larpix.quickstart as larpix_quickstart
from larpix.io.fakeio import FakeIO
from larpix.io.zmq_io import ZMQ_IO
import larpix.configs as configs
import larpix.larpix as larpix

from larpixdaq.packetformat import toBytes
from larpixdaq.routines.routines import ROUTINES, init_routines
from larpixdaq.logger_producer import DAQLogger


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
    board.load('controller/pcb-1_chip_info.json')
    current_boardname = 'pcb-1'
    board.logger = DAQLogger(producer)
    state = ''
    run = False
    configurations = {
            'startup': 'startup.json',
            'quiet': 'quiet.json',
    }
    def write_config(key, registers_str='', write_read_str='',
            message=''):
        '''
        write_config(key, registers='', write_read='', message='')

        Send the given configuration to the board.

        '''
        try:
            global board
            if registers_str:  # treat as int or list
                registers = ast.literal_eval(registers_str)
            else:
                registers = None
            if not write_read_str:
                write_read = 0
            if not message:
                message = None
            board.write_configuration(key, registers, write_read,
                    message)
            return 'success'
        except Exception as e:
            logging.exception(e)
            return 'ERROR: %s' % e

    def read_config(key, registers_str='', message=''):
        '''
        read_config(key, registers='', message='')

        Read configurations from the board.

        '''
        try:
            global board
            if registers_str:  # treat as int or list
                registers = ast.literal_eval(registers_str)
            else:
                registers = None
            if not message:
                message = None
            if isinstance(board.io, FakeIO):
                chip = board.get_chip(key)
                packets = chip.get_configuration_packets(
                        larpix.Packet.CONFIG_WRITE_PACKET)
                for p in packets:
                    p.packet_type = larpix.Packet.CONFIG_READ_PACKET
                    p.assign_parity()
                board.io.queue.append((packets, b'some bytes'))
            board.read_configuration(key, registers, message=message)
            packets = board.reads[-1]
            result = '\n'.join(str(p) for p in packets if p.packet_type
                    == p.CONFIG_READ_PACKET)
            return result
        except Exception as e:
            logging.exception(e)
            return 'ERROR: %s' % e
    def validate_config(key):
        '''
        validate_config(key)

        Read configurations from the board and compare to those stored
        in software, returning True if they're equal.

        '''
        try:
            global board
            if isinstance(board.io, FakeIO):
                chip = board.get_chip(key)
                packets = chip.get_configuration_packets(
                        larpix.Packet.CONFIG_WRITE_PACKET)
                for p in packets:
                    p.packet_type = larpix.Packet.CONFIG_READ_PACKET
                board.io.queue.append((packets, b'some bytes'))
            result = board.verify_configuration(key)
            return result
        except Exception as e:
            logging.exception(e)
            return 'ERROR: %s' % e
    def retrieve_config(key):
        '''
        retrieve_config(chipid)

        Return the current configuration stored in software for the
        given chip.

        '''
        try:
            global board
            chip = board.get_chip(key)
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
            for key, chip_updates in updates.items():
                chip = board.get_chip(key)
                chip.config.from_dict(chip_updates)
            return 'success'
        except Exception as e:
            logging.exception(e)
            return 'ERROR: %s' % e
    def get_boards():
        '''
        get_boards()

        List the available boards and chip keys, and the current board
        name.

        '''
        try:
            boards = [
                    'pcb-1',
                    'pcb-2',
                    'pcb-3',
                    'pcb-4',
                    'pcb-5',
                    'pcb-6',
                    'pcb-10',
                    ]
            board_data = []
            for boardname in boards:
                result = configs.load('controller/' + boardname +
                        '_chip_info.json')
                boarditem = {
                        'name': result['name'],
                        'chips': result['chip_list'],
                        }
                board_data.append(boarditem)
            return {'data': board_data, 'current': current_boardname}
        except Exception as e:
            logging.exception(e)
            return 'ERROR: %s' % e
    def load_board(filename):
        '''
        load_board(filename)

        Load the board (Controller) configuration located at the given
        filename.

        '''
        try:
            global board
            data = configs.load(filename)
            global current_boardname
            current_boardname = data['name']
            board.load(filename)
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
            init_routines()
            return [{
                'name': name,
                'params': [{'name': p, 'type': 'input'} for p in
                    r.params],
                }
                for name, r in ROUTINES.items()
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
            def send_data(packet_list, metadata=None):
                producer.produce(toBytes(packet_list), metadata)
                return
            global board
            board, result = ROUTINES[name].func(board, send_data,
                    producer.send_info, *args)
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
    init_routines()
    producer.register_action('write_config', write_config,
            write_config.__doc__)
    producer.register_action('read_config', read_config, read_config.__doc__)
    producer.register_action('validate_config', validate_config,
            validate_config.__doc__)
    producer.register_action('retrieve_config', retrieve_config,
            retrieve_config.__doc__)
    producer.register_action('send_config', send_config, send_config.__doc__)
    producer.register_action('get_boards', get_boards,
            get_boards.__doc__)
    producer.register_action('load_board', load_board,
            load_board.__doc__)
    producer.register_action('list_routines', list_routines,
            list_routines.__doc__)
    producer.register_action('run_routine', run_routine, run_routine.__doc__)
    producer.register_action('sleep', sleep, sleep.__doc__)
    producer.request_state()
    while True:
        producer.receive(0.25)
        if state != producer.state:
            print('State update: New state: %s' % producer.state)
            if state == 'RUN':
                producer.send_info('Ending run')
            state = producer.state
            if state == 'RUN':
                producer.send_info('Beginning run')
                producer.produce(toBytes([larpix.TimestampPacket(int(time.time()))]))
                fake_timestamp = 0
        if state == 'RUN':
            if not board.io.is_listening:
                logging.debug('about to start listening')
                board.start_listening()
            if isinstance(board.io, FakeIO):
                packets = []
                for _ in range(300):
                    p = larpix.Packet()
                    p.timestamp = fake_timestamp % 16777216
                    p.dataword = int(sum(random.random() for _ in range(256)))
                    chip = random.choice(list(board.chips.values()))
                    p.chipid = chip.chip_id
                    p.channel_id = random.randint(0, 31)
                    fake_timestamp += 1
                    p.assign_parity()
                    p.chip_key = '%d-%d-%d' % (1, 1, chip.chip_id)
                    packets.append(p)
                board.io.queue.append((packets, p.bytes() + b'\x00'))
            data = board.read()
        else:
            if board.io.is_listening:
                board.stop_listening()
finally:
    producer.cleanup()
