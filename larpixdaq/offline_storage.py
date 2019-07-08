import argparse

from moddaq import Consumer
from larpix.logger.h5_logger import HDF5Logger

from larpixdaq.packetformat import fromBytes

class OfflineStorage(object):
    '''
    Record all received packets in offline storage.

    '''

    def __init__(self, core):
        consumer_args = {
                'core_address': core + ':5551',
                'heartbeat_time_ms': 300,
        }
        self._consumer = Consumer(name='Offline storage',
                connections=['AGGREGATOR'], **consumer_args)
        self.state = ''

    def run(self):
        try:
            logger = None
            while True:
                messages = self._consumer.receive(None)
                if self.state != self._consumer.state:
                    if self._consumer.state == 'RUN':
                        logger = HDF5Logger(directory='runs')
                        logger.enable()
                        logger.open()
                        self._consumer.log('INFO', 'Storing data in file'
                        ' %s' % logger.filename)
                    if self._consumer.state != 'RUN':
                        if logger is not None:
                            logger.flush()
                            logger.disable()
                        logger = None
                    self.state = self._consumer.state
                for message in messages:
                    if message[0] == 'DATA':
                        _, metadata, data = message
                        packets = fromBytes(data)
                        logger.record(packets)
        finally:
            if logger is not None:
                logger.flush()
                logger.disable()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--core', default='tcp://127.0.0.1')
    args = parser.parse_args()
    offline_storage = OfflineStorage(args.core)
    try:
        offline_storage.run()
    finally:
        offline_storage._consumer.cleanup()
