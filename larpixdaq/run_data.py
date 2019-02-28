'''
Record packets from the current run and compute various statistics.

'''

import time
import logging

from moddaq import Consumer, protocol
from larpix.larpix import Packet

class RunData(object):
    '''
    Record packets from the current run and compute various statistics.

    '''

    def __init__(self, core):
        consumer_args = {
                'core_address': core + ':5550',
                'response_address': core + ':5551',
                'action_docs': {
                    'data_rate': '''data_rate()
                        Return the average data rate for the packets
                        received so far.''',
                }

        }
        self._consumer = Consumer(name='Run data', connections=['AGGREGATOR'],
                **consumer_args)
        self._consumer.actions['data_rate'] = self._data_rate
        self.packets = []
        self.start_time = 0
        return

    def _data_rate(self):
        '''
        Return the average data rate for the packets received so far.

        '''
        try:
            npackets = len(self.packets)
            time_elapsed = time.time() - self.start_time
            return str(npackets/time_elapsed)
        except Exception as e:
            logging.exception(e)
            return 'ERROR: %s' % e

    @staticmethod
    def parse_data(packet_bytes):
        splits = packet_bytes.split(b'\xAA\xAA')
        packets = [Packet(b) for b in splits]
        return packets

    def run(self):
        while True:
            messages = self._consumer.receive()
            for message in messages:
                if message[0] == 'DATA':
                    if self.start_time == 0:
                        self.start_time = time.time()
                    _, metadata, data = message
                    packets = self.parse_data(data)
                    self.packets.extend(packets)


if __name__ == '__main__':
    try:
        run_data = RunData('tcp://127.0.0.1')
        run_data.run()
    finally:
        run_data._consumer.cleanup()
