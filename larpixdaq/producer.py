from __future__ import absolute_import
from __future__ import print_function
import argparse
import logging
import time
import ast
import json
import random

from xylem import Producer
import larpix.quickstart as larpix_quickstart
from larpix.io.fakeio import FakeIO
from larpix.io.zmq_io import ZMQ_IO
from larpix.io.multizmq_io import MultiZMQ_IO
import larpix.configs as configs
import larpix.larpix as larpix

from larpixdaq.packetformat import toBytes
from larpixdaq.routines import ROUTINES, init_routines
from larpixdaq.logger_producer import DAQLogger

class LArPixProducer(object):
    """The entry point of LArPix data into the xylem DAQ pipeline.

    On initialization, the LArPixProducer object will be connected to
    the DAQ Core, loaded up with the ``'pcb-1'`` Controller
    configuration, connected to the appropriate IO instance, and set up
    with a ``larpix.logger.Logger`` subclass instance that logs all data
    into xylem (disabled on initialization, accessible at
    ``self.board.logger``).

    The producer is the component with direct contact into the LArPix
    environment. As such, the producer receives data from the data board
    and sends it into the DAQ chain. It also sends configuration
    commands to the LArPix ASICs and runs custom DAQ routines such as
    threshold scans and calibrations.

    Implementation-wise, this all happens via a larpix-control
    Controller object (not to be confused with the DAQ Controller).

    Custom routines can be implemented using the
    :py:mod:`larpixdaq.routines` package. Custom
    Routines are managed in a Routine object, in which you should store
    the routine name, function handle/reference, and list of parameters.
    (TODO!!! allow for documentation for custom routines.) Routines can
    access the DAQ functionality via their arguments controller,
    send_data, send_info. They can also accept additional arguments.
    Routines must return a tuple of (controller, result) where result is
    the output of the routine (e.g. a list of thresholds, or even simply
    the string "success") which must be JSON-serializable.

    :var producer: the xylem Producer object used to send data
    :var board: the ``larpix.larpix.Controller`` instance used to gather
        data
    :var current_boardname: the short name of the layout/configuration
        used for the Controller object, e.g. ``'pcb-1'``.
    :var state: the DAQ State of the xylem Producer component

    :param output_address: the full TCP address (including port number)
        that data will be published to
    :param core_address: the full TCP address (including port number) of
        the DAQ Core
    :param use_fakeio: ``True`` to use a ``FakeIO`` object rather than
        real data
    :param config_file: the file path of the IO configuration file to
        use with a ``ZMQ_IO`` object (unused if ``use_fakeio``)
    """

    def __init__(self, output_address, core_address, io_config):
        kwargs = {
                'core_address': core_address,
                'heartbeat_time_ms': 300,
        }
        self.producer = Producer(output_address, name='LArPix board', group='BOARD', **kwargs)
        self.board = larpix.Controller()
        io_class = io_config[0]
        if io_class == 'FakeIO':
            self.board.io = FakeIO()
        elif io_class == 'ZMQ_IO':
            config_file = io_config[1]
            self.board.io = ZMQ_IO(config_file)
        elif io_class == 'MultiZMQ_IO':
            config_file = io_config[1]
            self.board.io = MultiZMQ_IO(config_file)
        else:
            raise ValueError('Invalid IO class from --io-config: %s' %
                    io_config[0])
        self.board.load('controller/pcb-1_chip_info.json')
        self.current_boardname = 'pcb-1'
        self.board.logger = DAQLogger(self.producer)
        self.state = ''
        run = False
        configurations = {
                'startup': 'startup.json',
                'quiet': 'quiet.json',
        }
        ############
        # Routines #
        ############
        init_routines()
        self.producer.register_action(*self._get_register_action_args('write_config'))
        self.producer.register_action(*self._get_register_action_args('read_config'))
        self.producer.register_action(*self._get_register_action_args('validate_config'))
        self.producer.register_action(*self._get_register_action_args('retrieve_config'))
        self.producer.register_action(*self._get_register_action_args('send_config'))
        self.producer.register_action(*self._get_register_action_args('get_boards'))
        self.producer.register_action(*self._get_register_action_args('load_board'))
        self.producer.register_action(*self._get_register_action_args('list_routines'))
        self.producer.register_action(*self._get_register_action_args('run_routine'))
        self.producer.register_action(*self._get_register_action_args('sleep'))
        self.producer.request_state()

    def _get_register_action_args(self, name):
        """Return a tuple that can be passed as
        ``*self._get_register_action_args(name)`` to
        producer.register_action.

        :param name: the (string) name of the method to use for the
            routine. Doubles as the routine name.
        """
        method = getattr(self, name)
        return (name, method, method.__doc__)

    def write_config(self, key, registers_str=''):
        """Send the given configuration to the board.

        :param key: the chip key to send the configuration to
        :param registers_str: the configuration registers to send,
            specified as an int, a list of ints, or a string specifying a
            literal int or list of ints (e.g. ``'[1, 2, 10]'``).
        """
        if registers_str:  # treat as int or list
            registers = ast.literal_eval(registers_str)
        else:
            registers = None
        self.board.write_configuration(key, registers, 0, None)
        return 'success'

    def read_config(self, key, registers_str=''):
        """Read configurations from the board.

        :param key: the chip key to send the configuration to
        :param registers_str: the configuration registers to send,
            specified as an int, a list of ints, or a string specifying a
            literal int or list of ints (e.g. ``'[1, 2, 10]'``).
        """
        if registers_str:  # treat as int or list
            registers = ast.literal_eval(registers_str)
        else:
            registers = None
        if isinstance(self.board.io, FakeIO):
            chip = self.board.get_chip(key)
            packets = chip.get_configuration_packets(
                    larpix.Packet.CONFIG_WRITE_PACKET)
            for p in packets:
                p.packet_type = larpix.Packet.CONFIG_READ_PACKET
                p.assign_parity()
            self.board.io.queue.append((packets, b'some bytes'))
        self.board.read_configuration(key, registers, message=None)
        packets = self.board.reads[-1]
        result = '\n'.join(str(p) for p in packets if p.packet_type
                == p.CONFIG_READ_PACKET)
        return result

    def validate_config(self, key):
        """Read configurations from the board and compare to those stored
        in software, returning ``True`` if they're equal.

        :param key: the chip key whose configuration will be validated
        """
        if isinstance(self.board.io, FakeIO):
            chip = self.board.get_chip(key)
            packets = chip.get_configuration_packets(
                    larpix.Packet.CONFIG_WRITE_PACKET)
            for p in packets:
                p.packet_type = larpix.Packet.CONFIG_READ_PACKET
            self.board.io.queue.append((packets, b'some bytes'))
        result = self.board.verify_configuration(key)
        return result

    def retrieve_config(self, key):
        """Return the current configuration stored in software for the
        given chip.

        :param key: the chip key whose configuration will be retrieved
        """
        chip = self.board.get_chip(key)
        return chip.config.to_dict()

    def send_config(self, updates):
        """Apply the given updates to the software configuration.

        :param updates: a dict of configuration register updates
        compatible with ``larpix.larpix.Config.from_dict``.
        """
        for key, chip_updates in updates.items():
            chip = self.board.get_chip(key)
            chip.config.from_dict(chip_updates)
        return 'success'

    def get_boards(self):
        """List the available boards and chip keys, and the current board
        name.
        """
        boards = [
                'pcb-1',
                'pcb-2',
                'pcb-3',
                'pcb-4',
                'pcb-5',
                'pcb-6',
                'pcb-10',
                ]
        board_data = []
        for boardname in boards:
            result = configs.load('controller/' + boardname +
                    '_chip_info.json')
            boarditem = {
                    'name': result['name'],
                    'chips': result['chip_list'],
                    }
            board_data.append(boarditem)
        return {'data': board_data, 'current': self.current_boardname}

    def load_board(self, filename):
        """Load the board (Controller) configuration located at the given
        filename.

        :param filename: the file name to load. If using a pre-installed
            configuration, the file name must begin with the standard
            ``'controller/'`` directory prefix.
        """
        data = configs.load(filename)
        self.current_boardname = data['name']
        self.board.load(filename)
        return 'success'

    @staticmethod
    def list_routines():
        """List the available routines."""
        init_routines()
        return [{
            'name': name,
            'params': [{'name': p, 'type': 'input'} for p in
                r.params],
            }
            for name, r in ROUTINES.items()
            ]

    def run_routine(self, name, *args):
        """Run the given routine.

        :param name: the name of the routine to run
        :param args: all subsequent arguments are passed in order to the
            routine as parameters
        """
        def send_data(packet_list, metadata=None):
            self.producer.produce(toBytes(packet_list), metadata)
            return
        self.board, result = ROUTINES[name].func(self.board, send_data,
                self.producer.send_info, *args)
        return result

    @staticmethod
    def sleep(time_in_sec):
        """Sleep and return success."""
        delay = int(time_in_sec)
        time.sleep(delay)
        return 'success'

    def run(self):
        """Event loop of checking for DAQ commands, checking for new
        data, and repeating.

        If the DAQ State is RUN, the data logger will be enabled so that
        newly-arrived data will be sent to the xylem pipeline. In all
        other DAQ States, the data logger will be disabled so data will
        not be send down the pipeline.

        If the IO object on ``self.board`` is a FakeIO object, fake data
        will be generated to mimic data arriving from the LArPix board.
        """
        while True:
            self.producer.receive(0.25)
            if self.state != self.producer.state:
                old_state = self.state
                new_state = self.producer.state
                print('State update: New state: %s' % new_state)
                if old_state == 'RUN':
                    self.producer.send_info('Ending run')
                    self.board.logger.disable()
                if new_state == 'RUN':
                    self.producer.send_info('Beginning run')
                    self.board.logger.enable()
                    fake_timestamp = 0
                self.state = self.producer.state
            if self.state == 'RUN':
                if not self.board.io.is_listening:
                    logging.debug('about to start listening')
                    self.board.start_listening()
                if isinstance(self.board.io, FakeIO):
                    packets = []
                    for _ in range(300):
                        p = larpix.Packet()
                        p.timestamp = fake_timestamp % 16777216
                        p.dataword = int(sum(random.random() for _ in range(256)))
                        chip = random.choice(list(self.board.chips.values()))
                        p.chipid = chip.chip_id
                        p.channel_id = random.randint(0, 31)
                        fake_timestamp += 1
                        p.assign_parity()
                        p.chip_key = '%d-%d-%d' % (1, 1, chip.chip_id)
                        packets.append(p)
                    self.board.io.queue.append((packets, p.bytes() + b'\x00'))
                data = self.board.read()
            else:
                if self.board.io.is_listening:
                    self.board.stop_listening()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Launch the data '
        'interface between LArPix and the xylem DAQ pipeline')
    parser.add_argument('address',
            help='The address to publish data to including port number')
    parser.add_argument('--core', default='tcp://127.0.0.1',
            help='The address of the DAQ Core, not including port number')
    parser.add_argument('-d', '--debug', action='store_true',
            help='Enter debug (verbose) mode')
    parser.add_argument('--io-config', nargs='+', required=True,
            help='<IO class> [<IO config file>], e.g. "ZMQ_IO io/default.json"')
    args = parser.parse_args()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    address = args.address
    core_url = args.core
    core_address = core_url + ':5551'
    producer = LArPixProducer(address, core_address, args.io_config)
    try:
        producer.run()
    except KeyboardInterrupt:
        pass
    finally:
        producer.producer.cleanup()
