'''
Record packets from the current run and compute various statistics.

'''

import time
import logging
import base64

from moddaq import Consumer, protocol
from larpix.larpix import Packet

import larpixdaq.packetformat as pformat

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
                    'packets': '''packets()
                        Return the packets as a bytestream with a 2-byte
                        delimiter of 0xAAAA.''',
                }

        }
        self._consumer = Consumer(name='Run data', connections=['AGGREGATOR'],
                **consumer_args)
        self._consumer.actions['data_rate'] = self._data_rate
        self._consumer.actions['packets'] = self._packets
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

    def _packets(self):
        '''
        Return a bytestream of all the packets received, converted to a
        string in base64 encoding.

        '''
        try:
            return pformat.to_unicode_coding(self.packets)
        except Exception as e:
            logging.exception(e)
            return 'ERROR: %s' % e

    def run(self):
        while True:
            messages = self._consumer.receive(1)
            for message in messages:
                if message[0] == 'DATA':
                    if self.start_time == 0:
                        self.start_time = time.time()
                    _, metadata, data = message
                    packets = pformat.fromBytes(data)
                    self.packets.extend(packets)


if __name__ == '__main__':
    try:
        run_data = RunData('tcp://127.0.0.1')
        run_data.run()
    finally:
        run_data._consumer.cleanup()
