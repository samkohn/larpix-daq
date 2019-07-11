import argparse

from xylem import Consumer
from xylem.EventHandler import EventHandler
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
        self._consumer.addHandler(EventHandler('data_message',
            self.handle_new_data))
        self.logger = None

    def handle_new_data(self, origin, header, data):
        if self.state == 'RUN' or self.state == 'READY':
            packets = fromBytes(data)
            self.logger.record(packets)
        else:
            return

    def run(self):
        try:
            while True:
                messages = self._consumer.receive(None)
                if self.state != self._consumer.state:
                    old_state = self.state
                    new_state = self._consumer.state
                    if old_state == 'RUN':
                        if self.logger is not None:
                            self.logger.flush()
                            self.logger.disable()
                            self.logger = None
                    if new_state == 'READY':
                        self.logger = HDF5Logger(directory='runs')
                        self.logger.enable()
                        self._consumer.log('INFO', 'Storing data in file'
                                ' %s' % self.logger.filename)
                    self.state = new_state
        finally:
            if self.logger is not None:
                self.logger.flush()
                self.logger.disable()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--core', default='tcp://127.0.0.1')
    args = parser.parse_args()
    offline_storage = OfflineStorage(args.core)
    try:
        offline_storage.run()
    except KeyboardInterrupt:
        pass
    finally:
        offline_storage._consumer.cleanup()
