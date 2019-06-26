'''
Record packets from the current run and compute various statistics.

'''

import time
import logging
from collections import deque

import requests
from moddaq import Consumer, protocol
from larpix.larpix import Packet

import larpixdaq.packetformat as pformat

class RunData(object):
    '''
    Record packets from the current run and compute various statistics.

    '''

    def __init__(self, core):
        consumer_args = {
                'core_address': core + ':5551',
                'heartbeat_time_ms': 300,
                'action_docs': {
                    'data_rate': '''data_rate()
                        Return the average data rate for the packets
                        received so far.''',
                    'packets': '''packets()
                        Return the packets as a bytestream with a 2-byte
                        delimiter of 0xAAAA.''',
                    'messages': '''messages()
                        Return the messages.''',
                }

        }
        self._consumer = Consumer(name='Run data', connections=['AGGREGATOR'],
                **consumer_args)
        self._consumer.actions['data_rate'] = self._data_rate
        self._consumer.actions['packets'] = self._packets
        self._consumer.actions['messages'] = self._messages
        self.packets = []
        self.timestamps = []
        self.messages = []
        self.datarates = deque([], 100)
        self.datarate_timestamps = deque([], 100)
        self.start_time = 0
        self._sent_index = 0
        self.runno = 0
        self.state = self._consumer.state
        return

    def _data_rate(self):
        '''
        Return the average data rate for the packets received so far.

        '''
        try:
            npackets = len(self.packets)
            time_elapsed = time.time() - self.start_time
            return '%.2f' % (npackets/time_elapsed)
        except Exception as e:
            logging.exception(e)
            return 'ERROR: %s' % e

    def _packets(self):
        '''
        Return a bytestream of all the packets received, converted to a
        string in base64 encoding.

        '''
        try:
            return pformat.toDict(self.packets)
        except Exception as e:
            logging.exception(e)
            return 'ERROR: %s' % e

    def _messages(self):
        '''
        Return the messages.

        '''
        try:
            return self.messages
        except Exception as e:
            logging.exception(e)
            return 'ERROR: %s' % e

    def _begin_run(self):
        self.start_time = time.time()
        self.packets = []
        self.datarates.clear()
        self.datarate_timestamps.clear()
        self.runno += 1

    def _end_run(self):
        pass

    def run(self):
        t_last_send = time.time()
        try:
            r = requests.post('http://localhost:5000/packets', json={'rate':0,
                'packets':[]})
        except:
            pass
        while True:
            messages = self._consumer.receive(1)
            next_tick = False
            if self.state != self._consumer.state:
                if self._consumer.state == 'RUN':
                    self._begin_run()
                elif self.state == 'RUN':
                    self._end_run()
                self.state = self._consumer.state
            for message in messages:
                if message[0] == 'DATA':
                    _, metadata, data = message
                    packets = pformat.fromBytes(data)
                    self.packets.extend(packets)
                    new_timestamp = int(time.time())
                    if len(self.timestamps) > 0:
                        last_packet_timestamp = self.timestamps[-1]
                    else:
                        last_packet_timestamp = new_timestamp
                    next_tick = last_packet_timestamp != new_timestamp
                    self.timestamps.extend([new_timestamp]*len(packets))
                elif message[0] == 'INFO':
                    _, header, info_message = message
                    self.messages.append(info_message)
                    if (header['component'] == 'LArPix board'
                            and info_message == 'Beginning run'):
                        self._consumer.log('INFO', 'Received start message')
                    elif (header['component'] == 'LArPix board'
                            and info_message == 'Ending run'):
                        self._consumer.log('INFO', 'Received end message')

            if self.state == 'RUN' and next_tick:
                packets_last_second = (
                        self.timestamps.count(last_packet_timestamp))
                self.datarates.append(packets_last_second)
                self.datarate_timestamps.append(last_packet_timestamp)
                try:
                    r = requests.post('http://localhost:5000/packets',
                            json={'rate':self._data_rate(),
                                'packets':self._packets()[-100:][::-1],
                                'rate_list':list(self.datarates),
                                'rate_times':list(self.datarate_timestamps),})
                except requests.ConnectionError as e:
                    self._consumer.log('DEBUG', 'Failed to send packets '
                            'to server: %s ' % e)




if __name__ == '__main__':
    try:
        run_data = RunData('tcp://127.0.0.1')
        run_data.run()
    finally:
        run_data._consumer.cleanup()
