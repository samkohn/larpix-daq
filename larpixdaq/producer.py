from __future__ import absolute_import
from __future__ import print_function
import argparse
from moddaq import Producer
import larpix.larpix as larpix

try:
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--address', default='tcp://127.0.0.1')
    args = parser.parse_args()
    base_url = args.address
    core_address = base_url + ':5550'
    response_address = base_url + ':5551'
    kwargs = {
            'core_address': core_address,
            'response_address': response_address,
    }
    producer = Producer('producer-aggregator', name='LArPix board',
            group='BOARD', **kwargs)
    board = larpix.Controller()
    board._serial._keep_open = True
    state = ''
    producer.request_state()
    while True:
        producer.receive(0)
        if state != producer.state:
            print('State update: New state: %s' % producer.state)
            state = producer.state
        if state == b'RUN':
            board.run(0.5, 'run')
            packets = b''.join(p.bytes() for p in board.reads[-1])
            producer.produce(packets)
finally:
    producer.cleanup()
