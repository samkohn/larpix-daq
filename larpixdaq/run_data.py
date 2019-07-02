'''
Record packets from the current run and compute various statistics.

'''

import time
import logging
from collections import deque, defaultdict
import json

import requests
from moddaq import Consumer, protocol
from larpix.larpix import Packet
from larpixgeometry import layouts

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
        self._consumer.register_action('data_rate', self._data_rate,
                self._data_rate.__doc__)
        self._consumer.register_action('packets', self._packets,
                self._packets.__doc__)
        self._consumer.register_action('messages', self._messages,
                self._messages.__doc__)
        self._consumer.register_action('retrieve_pixel_layout',
                self.retrieve_pixel_layout, self.retrieve_pixel_layout.__doc__)
        self._consumer.register_action('load_pixel_layout',
                self.load_pixel_layout, self.load_pixel_layout.__doc__)
        self.packets = deque([], 100000)
        self.timestamps = defaultdict(int)
        self.pixel_rates=defaultdict(([0]*832).copy)
        self.max_pixel_rates = [0]*832
        self.messages = []
        self.datarates = deque([], 100)
        self.datarate_timestamps = deque([], 100)
        self.adcs = deque([], 1000)
        self.start_time = 0
        self._sent_index = 0
        self.runno = 0
        self.state = self._consumer.state
        self.layout = {'chips':[], 'pixels':[]}
        self.pixel_lookup = {}
        return

    def create_pixel_lookup(self, chip_pixel_list):
        '''
        Create a pixel lookup from a given list of chip-pixel
        assignments.

        chip_pixel_list is of the form

        ```
        [
          [chip0id, [ch0pixel, ch1pixel, ...]],
          [chip1id, [ch0pixel, ch1pixel, ...]],
          ...
        ]
        ```

        '''
        pixel_lookup = {}
        for (chipid, pixels) in chip_pixel_list:
            pixel_lookup[chipid] = pixels
        return pixel_lookup

    def create_chip_lookup(self, chip_pixel_list):
        '''
        Create a chip+channel lookup based on pixel ID.

        The input chip_pixel_list is of the form

        ```
        [
          [chip0id, [ch0pixel, ch1pixel, ...]],
          [chip1id, [ch0pixel, ch1pixel, ...]],
          ...
        ]
        ```

        The output is of the form

        ```
        {
          pixel0id: {'channel': pixel0channel, 'chip': pixel0chip},
          pixel1id: {'channel': pixel1channel, 'chip': pixel1chip},
          ...
        }
        ```

        '''
        chip_lookup = {}
        for (chipid, pixels) in chip_pixel_list:
            for (channelid, pixelid) in enumerate(pixels):
                chip_lookup[pixelid] = {
                        'channel': channelid,
                        'chip': chipid,
                        }
        return chip_lookup

    def retrieve_pixel_layout(self):
        '''
        retrieve_pixel_layout()

        Return the current pixel layout and pixel->{chip, channel}
        mapping.

        '''
        try:
            return {
                    'layout': self.layout,
                    'lookup': self.chip_lookup,
                    }
        except Exception as e:
            logging.exception(e)
            return 'ERROR: %s' % e

    def load_pixel_layout(self, name):
        '''
        load_pixel_layout(name)

        Retrieve and store the pixel layout from larpix-geometry.

        '''
        try:
            self.layout = layouts.load(name)
            for entry in self.layout['chips']:
                entry[0] = '1-1-%d' % entry[0]
            self.pixel_lookup = self.create_pixel_lookup(self.layout['chips'])
            self.chip_lookup = self.create_chip_lookup(self.layout['chips'])
            return {
                    'layout': self.layout,
                    'lookup': self.chip_lookup,
                    }
        except Exception as e:
            logging.exception(e)
            return 'ERROR: %s' % e

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
        self.packets.clear()
        self.datarates.clear()
        self.datarate_timestamps.clear()
        self.pixel_rates.clear()
        self.max_pixel_rates = [0] * 832
        self.adcs.clear()
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
        last_second = int(time.time())
        while True:
            messages = self._consumer.receive(1)
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
                    now = int(time.time())
                    self.timestamps[now] += len(packets)
                    pixel_rates_now = self.pixel_rates[now]
                    for packet in packets:
                        if packet.packet_type == Packet.DATA_PACKET:
                            chip_key = str(packet.chip_key)
                            channelid = packet.channel_id
                            pixel_list = self.pixel_lookup.get(chip_key, None)
                            if pixel_list is not None:
                                pixelid = pixel_list[channelid]
                                if pixelid is not None:
                                    pixel_rates_now[pixelid] += 1
                                    if (pixel_rates_now[pixelid] >
                                            self.max_pixel_rates[pixelid]):
                                        self.max_pixel_rates[pixelid] = (
                                                pixel_rates_now[pixelid])
                    self.adcs.extend(p.dataword for p in packets if
                            p.packet_type == Packet.DATA_PACKET)
                elif message[0] == 'INFO':
                    _, header, info_message = message
                    self.messages.append(info_message)
                    if (header['component'] == 'LArPix board'
                            and info_message == 'Beginning run'):
                        self._consumer.log('INFO', 'Received start message')
                    elif (header['component'] == 'LArPix board'
                            and info_message == 'Ending run'):
                        self._consumer.log('INFO', 'Received end message')

            now = int(time.time())
            next_tick = now != last_second
            if self.state == 'RUN' and next_tick:
                self.datarates.append(self.timestamps[last_second])
                self.datarate_timestamps.append(last_second)
                pixel_rates_last_second = self.pixel_rates[last_second][:]
                del self.timestamps[last_second]
                del self.pixel_rates[last_second]
                last_second = now
                try:
                    r = requests.post('http://localhost:5000/packets',
                            json={'rate':self._data_rate(),
                                'packets':self._packets()[-100:][::-1],
                                'rate_list':list(self.datarates),
                                'rate_times':list(self.datarate_timestamps),
                                'adcs': list(self.adcs),
                                'rate_bypixel': pixel_rates_last_second,
                                'maxrate_bypixel': self.max_pixel_rates,
                                })
                except requests.ConnectionError as e:
                    self._consumer.log('DEBUG', 'Failed to send packets '
                            'to server: %s ' % e)





if __name__ == '__main__':
    try:
        run_data = RunData('tcp://127.0.0.1')
        run_data.run()
    finally:
        run_data._consumer.cleanup()
