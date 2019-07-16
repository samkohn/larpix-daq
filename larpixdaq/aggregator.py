import logging
import argparse
import time

from xylem import Aggregator
from larpix.larpix import Controller, Packet

from larpixdaq.packetformat import fromBytes

class LArPixAggregator(object):
    """The data aggregator for LArPix.

    The aggregator connects the producer (LArPix board) to any number of
    data consumers such as data monitor and offline storage.

    In the future, the aggregator will support receiving data from
    multiple LArPix boards.

    Example invocation::

        python -m larpixdaq.aggregator tcp://127.0.0.1:5002

    :var aggregator: the xylem Aggregator object
    :var state: the DAQ state of the xylem Aggregator component

    :param output_address: the full TCP address (including port number)
        that data will be published to
    :param core_address: the full TCP address (including port number) of
        the DAQ core
    """

    def __init__(self, output_address, core_address):
        kwargs = {
                'core_address': core_address,
                'heartbeat_time_ms': 300,
                }
        self.aggregator = Aggregator(output_address, name='LArPix aggregator',
                connections=['BOARD'], **kwargs)
        self.aggregator.request_state()
        self.state = self.aggregator.state

    def run(self):
        """Initiate the event loop of reading and rebroadcasting
        messages and data.
        """
        while True:
            messages = self.aggregator.receive(1)
            for message in messages:
                if message[0] == 'DATA':
                    _, metadata, data = message
                    self.aggregator.broadcast(metadata, data)
                elif message[0] == 'INFO':
                    self.aggregator.log('DEBUG', 'Rebroadcasting (%s, %s)' %
                            (message[1], message[2]))
                    self.aggregator.rebroadcast_info(message[1], message[2])
            if self.state != self.aggregator.state:
                self.aggregator.log('DEBUG', 'State update. New state: %s' % aggregator.state)
                self.state = self.aggregator.state

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Launch the data '
            'aggregator for LArPix DAQ')
    parser.add_argument('address',
            help='The address to publish data to including port number')
    parser.add_argument('--core', default='tcp://127.0.0.1',
            help='The address of the DAQ Core, not including port number')
    parser.add_argument('-d', '--debug', action='store_true',
            help='Enter debug (verbose) mode')
    args = parser.parse_args()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    aggregator = LArPixAggregator(args.address, args.core + ':5551')
    try:
        aggregator.run()
    except KeyboardInterrupt:
        pass
    finally:
        aggregator.aggregator.cleanup()
