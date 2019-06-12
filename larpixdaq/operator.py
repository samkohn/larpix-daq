'''
The operator interface for the LArPix DAQ system.

'''
import moddaq

end_receive_loop_headers = {
        'ACTIONS',
        'ACTION RESULT',
        'STATE',
        'STATE REQUEST',
        'CLIENTS',
        }

class Operator(object):
    '''
    The Operator class handles all of the needs of an DAQ operator:
    start/end runs, load/validate configurations, run calibrations,
    examine data samples and data rates, etc.

    The methods that have ``chip``, ``channel``, or ``chip_or_channel``
    as parameters take in ``Chip`` or ``Channel`` objects that specify
    a unique physical ASIC or electronics channel.

    '''

    def __init__(self, address=None):
        if address is None:
            address = 'tcp://127.0.0.1:5551'
        self.chips = None
        self.geometry = None
        self.run_number = 0
        self.is_running = False
        self.routines = []
        self.configurations = {}
        self._controller = moddaq.Controller(address)

    def cleanup(self):
        self._controller.cleanup()

    def _receive_loop(self, timeout=None):
        header = None
        max_loops = 10
        nloops = 0
        while (header not in end_receive_loop_headers
                and nloops < max_loops):
            result = self._controller.receive(timeout)
            nloops += 1
            if result is not None:
                header = result['header']
                yield result
        if result is None:
            yield None

    def get_boards(self, timeout=None):
        self._controller.send_action('LArPix board', 'get_boards', [])
        for result in self._receive_loop(timeout):
            yield result

    def load_board(self, filename, timeout=None):
        self._controller.send_action('LArPix board', 'load_board',
                [filename])
        for result in self._receive_loop(timeout):
            yield result

    ### Configurations

    def configure_chip(self, chip, name, value, channel='', timeout=None):
        '''
        Set the configuration in software for the specified ASIC.

        '''
        self._controller.send_action('LArPix board', 'configure_chip',
                [chip, name, value, channel])
        for result in self._receive_loop(timeout):
            yield result

    def write_configuration(self, chip, timeout=None):
        '''
        Send the configuration values from software onto the ASIC.

        '''
        self._controller.send_action('LArPix board', 'write_config',
                [chip])
        for result in self._receive_loop(timeout):
            yield result

    def read_configuration(self, chip, timeout=None):
        '''
        Read the configuration values from the ASIC.

        '''
        self._controller.send_action('LArPix board', 'read_config',
                [chip])
        for result in self._receive_loop(timeout):
            yield result

    def load_configuration(self, name):
        '''
        Load the given configuration onto the LArPix ASICs.

        '''
        action_ids = []
        for (chipid, iochain) in self.chips:
            new_id = self._controller.send_action('LArPix board',
                    'configure_name', [name, chipid, iochain])
            action_ids.append(new_id)
        for (chipid, iochain) in self.chips:
            new_id = self._controller.send_action('LArPix board',
                    'write_config', [chipid])
            action_ids.append(new_id)
        return action_ids

    def validate_configuration(self, chip, timeout=None):
        '''
        Read the configuration from the specified LArPix ASIC and return
        ``(True/False, {name: (actual, stored)})``.

        '''
        self._controller.send_action('LArPix board', 'validate_config',
                [chip])
        for result in self._receive_loop(timeout):
            yield result

    def learn_configuration(self):
        '''
        Read the configuration from all of the LArPix ASICs and store
        the actual values in software, replacing the existing values.

        '''
        action_ids = []
        for (chipid, iochain) in self.chips:
            action_id = self._controller.send_action('LArPix board',
            'learn_config', [chipid])
            action_ids.append(action_id)
        return action_ids

    def fetch_configurations(self):
        '''
        Return a list of available configurations.

        '''
        action_id = self._controller.send_action('LArPix board',
                'fetch_configs', [])
        return action_id

    def retrieve_configuration(self, chip, timeout=None):
        '''
        Return a dict of the current configuration stored in software
        for the given chipid.

        '''
        self._controller.send_action('LArPix board', 'retrieve_config',
                [chip])
        for result in self._receive_loop():
            yield result

    def send_configuration(self, updates, timeout=None):
        '''
        Send the given configuration updates to the LArPix control
        software.

        Updates should be a dict with keyed by chip ID.

        '''
        self._controller.send_action('LArPix board', 'send_config',
                [updates])
        for result in self._receive_loop():
            yield result


    ### Calibrations

    def list_routines(self):
        '''
        Return a list of routines/calibrations.

        '''
        self._controller.send_action('LArPix board',
                'list_routines', [])
        for result in self._receive_loop():
            yield result

    def run_routine(self, name, *args, timeout=None):
        '''
        Run the given routine and return the routine's output.

        '''
        self._controller.send_action('LArPix board',
                'run_routine', [name] + list(args))
        for result in self._receive_loop(timeout):
            yield result


    ### Physics runs

    def prepare_physics_run(self):
        '''
        Enter the "READY" DAQ state so that all DAQ components are ready
        to begin the physics run.

        '''
        self._controller.request_state_change('READY')
        return self._controller.receive(None)

    def begin_physics_run(self):
        '''
        Begin taking physics data, activate online data monitoring and
        analytics, and store the data in offline storage.

        '''
        self._controller.request_state_change('RUN')
        return self._controller.receive(None)


    def end_physics_run(self):
        '''
        Stop taking physics data, deactivate online data monitoring and
        analytics, and finalize the offline storage.

        '''
        self._controller.request_state_change('READY')
        return self._controller.receive(None)

    def run_info(self):
        '''
        Fetch current run info such as run number, start time, average
        data rate, etc.

        '''
        pass

    def data_rate(self, start_time, end_time, chip_or_channel,
            timeout=None):
        '''
        Return the data rate for the specified ASIC or channel between
        ``start_time`` and ``end_time``, as long as it's within the
        current run.

        '''
        self._controller.send_action('Run data', 'data_rate', [])
        for result in self._receive_loop(timeout):
            yield result

    def fetch_packets(self, start_time, end_time, chip_or_channel,
            timeout=None):
        '''
        Return all the packets produced by the specified ASIC or channel
        between ``start_time`` and ``end_time``, as long as they're from
        the current run.

        '''
        self._controller.send_action('Run data', 'packets', [])
        for result in self._receive_loop(timeout):
            yield result

    def fetch_messages(self, timeout=None):
        '''
        Return the messages produced by the DAQ system.

        '''
        self._controller.send_action('Run data', 'messages', [])
        for result in self._receive_loop(timeout):
            yield result

    def enable_channel(self, channel):
        '''
        Enable the given channel/pixel for data taking, overriding the
        current ASIC configuration.

        '''
        pass

    def disable_channel(self, channel):
        '''
        Disable the given channel/pixel so it will not produce any
        packets, overriding the current ASIC configuration.

        '''
        pass

