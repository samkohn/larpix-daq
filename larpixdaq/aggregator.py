import logging
import argparse
import time

from moddaq import Aggregator
from larpix.larpix import Controller, Packet

from larpixdaq.packetformat import fromBytes

try:
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('address', help='the address to bind to')
    parser.add_argument('--core', default='tcp://127.0.0.1')
    args = parser.parse_args()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    kwargs = {
            'core_address': args.core + ':5550',
            'response_address': args.core + ':5551',
            'heartbeat_time_ms': 300,
    }
    aggregator = Aggregator(args.address, name='LArPix aggregator',
            connections=['BOARD'], **kwargs)
    aggregator.request_state
    state = aggregator.state
    while True:
        messages = aggregator.receive(1)
        for message in messages:
            if message[0] == 'DATA':
                _, metadata, data = message
                print('received %d bytes' % len(data))
                print('%s' % repr(data[:20]))
                packets = fromBytes(data)
                print('received %d packets' % len(packets))
                metadata['agg_timestamp'] = time.time()
                aggregator.broadcast(metadata, data)
        if state != aggregator.state:
            print('State update. New state: %s' % aggregator.state)
            state = aggregator.state
finally:
    aggregator.cleanup()
