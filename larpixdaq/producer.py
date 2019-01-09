from __future__ import absolute_import
from __future__ import print_function
import argparse
import logging
import time
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
    }
    producer = Producer(address, name='LArPix board', group='BOARD', **kwargs)
    board = larpix.Controller()
    board._serial._keep_open = True
    state = ''
    producer.request_state()
    while True:
        producer.receive(0.4)
        if state != producer.state:
            print('State update: New state: %s' % producer.state)
            state = producer.state
        if state == b'RUN':
            logging.debug('about to run')
            data = board.serial_read(0.5)
            logging.debug('just took data')
            metadata = {'name': 'LArPix board', 'timestamp':
                    time.time()}
            logging.debug('producing packets: %s...' % repr(data[:20]))
            producer.produce(metadata, data)
finally:
    producer.cleanup()
