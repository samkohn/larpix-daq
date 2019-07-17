import argparse

from xylem import Consumer
from xylem.EventHandler import EventHandler
from larpix.logger.h5_logger import HDF5Logger

from larpixdaq.packetformat import fromBytes

class OfflineStorage(object):
    """Record all received packets in offline storage.

    The offline storage script stores LArPix data to disk using the
    LArPix+HDF5 file format.

    :var consumer: the xylem Consumer object used to receive data
    :var state: the DAQ State of the xylem Consumer component
    :var logger: the LArPix Logger object used to save data to disk. Can
        be ``None`` if current state is not READY or RUN.

    :param core_address: the full TCP address (including port number) of
        the DAQ core
    """

    def __init__(self, core_address):
        consumer_args = {
                'core_address': core_address,
                'heartbeat_time_ms': 300,
        }
        self.consumer = Consumer(name='Offline storage',
                connections=['AGGREGATOR'], **consumer_args)
        self.state = ''
        self.consumer.addHandler(EventHandler('data_message',
            self.handle_new_data))
        self.logger = None

    def handle_new_data(self, origin, header, data):
        """Save new data to disk.

        Parameters are defined by the ``xylem.EventHandler`` interface.
        """
        if ((self.state == 'RUN' or self.state == 'READY')
                and self.logger is not None):
            packets = fromBytes(data)
            self.logger.record(packets)
        else:
            return

    def run(self):
        """Initiate the event loop of reading and saving data."""
        try:
            while True:
                messages = self.consumer.receive(None)
                if self.state != self.consumer.state:
                    old_state = self.state
                    new_state = self.consumer.state
                    if old_state == 'RUN':
                        if self.logger is not None:
                            self.logger.flush()
                            self.logger.disable()
                            self.logger = None
                    if new_state == 'READY':
                        self.logger = HDF5Logger(directory='runs')
                        self.logger.enable()
                        self.consumer.log('INFO', 'Storing data in file'
                                ' %s' % self.logger.filename)
                    self.state = new_state
        finally:
            if self.logger is not None:
                self.logger.flush()
                self.logger.disable()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Launch the data '
            'consumer to save LArPix data to disk')
    parser.add_argument('--core', default='tcp://127.0.0.1',
            help='The address of the DAQ Core, not including port number')
    args = parser.parse_args()
    offline_storage = OfflineStorage(args.core + ':5551')
    try:
        offline_storage.run()
    except KeyboardInterrupt:
        pass
    finally:
        offline_storage.consumer.cleanup()
