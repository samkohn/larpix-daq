from __future__ import absolute_import
from __future__ import print_function
import argparse
import logging
import time
import ast
from moddaq import Producer
import larpix.larpix as larpix

try:
    parser = argparse.ArgumentParser()
    parser.add_argument('address')
    parser.add_argument('--core', default='tcp://127.0.0.1')
    parser.add_argument('-d', '--debug', action='store_true')
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
            'action_docs': {
                'begin_run': 'start taking data',
                'end_run': 'stop taking data',
                'configure_chip': '''configure_chip(chipid, name, value,
                    channel='')
                    Update the configuration stored in software.''',
                'write_config': '''write_config(chipid, registers='',
                    write_read='', message='')
                    Send the configuration from software to the board.''',
            },
    }
    producer = Producer(address, name='LArPix board', group='BOARD', **kwargs)
    try:
        board = larpix.Controller()
    except OSError:
        board = larpix.Controller('test')
        logging.info('Starting up larpix.Controller(\'test\')')
    board.use_all_chips = True
    board._serial._keep_open = True
    state = ''
    run = False
    def begin_run():
        global run, state
        if state == 'RUN':
            run = True
            return 'success'
        else:
            return 'ERROR: must be in state \'RUN\''
    def end_run():
        global run
        run = False
        return 'success'
    def configure_chip(chipid_str, name_str, value_str, channel_str=''):
        '''
        Update the chip configuration stored in software.

        '''
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
    def write_config(chipid_str, registers_str='', write_read_str='',
            message=''):
        '''
        Send the given configuration to the board.

        '''
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
    producer.actions['begin_run'] = begin_run
    producer.actions['end_run'] = end_run
    producer.actions['configure_chip'] = configure_chip
    producer.actions['write_config'] = write_config
    producer.request_state()
    while True:
        producer.receive(0.4)
        if state != producer.state:
            print('State update: New state: %s' % producer.state)
            state = producer.state
        logging.debug('run = %s', run)
        if state == 'RUN' and run:
            logging.debug('about to run')
            data = board.serial_read(0.5)
            logging.debug('just took data')
            metadata = {'name': 'LArPix board', 'timestamp':
                    time.time()}
            logging.debug('producing packets: %s...' % repr(data[:20]))
            producer.produce(metadata, data)
finally:
    producer.cleanup()
