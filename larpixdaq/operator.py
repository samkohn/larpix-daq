'''
The operator interface for the LArPix DAQ system.

'''
import moddaq

class Operator(object):
    '''
    The Operator class handles all of the needs of an DAQ operator:
    start/end runs, load/validate configurations, run calibrations,
    examine data samples and data rates, etc.

    The methods that have ``chip``, ``channel``, or ``chip_or_channel``
    as parameters take in ``Chip`` or ``Channel`` objects that specify
    a unique physical ASIC or electronics channel.

    '''

    def __init__(self):
        self.chips = None
        self.geometry = None
        self.run_number = 0
        self.is_running = False
        self.routines = []
        self.configurations = {}
        self._controller = moddaq.Controller('tcp://127.0.0.1:5551')


    ### Configurations

    def configure_chip(self, chip, name, value, channel=''):
        '''
        Set the configuration in software for the specified ASIC.

        '''
        self._controller.send_action('LArPix board', 'configure_chip',
                [chip, name, value, channel])
        for _ in range(2):
            yield self._controller.receive(None)

    def write_configuration(self, chip):
        '''
        Send the configuration values from software onto the ASIC.

        '''
        self._controller.send_action('LArPix board', 'write_config',
                [chip])
        for _ in range(2):
            yield self._controller.receive(None)


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

    def validate_configuration(self):
        '''
        Read the configuration from all of the LArPix ASICs and return
        ``True`` if the actual values match those stored in software.

        '''
        for (chipid, iochain) in self.chips:
            action_id = self._controller.send_action('LArPix board',
                    'validate_config', [chipid])

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


    ### Calibrations

    def list_routines(self):
        '''
        Return a list of routines/calibrations.

        '''
        action_id = self._controller.send_action('LArPix board',
                'list_routines', [])
        return action_id

    def run_routine(self, name, *args):
        '''
        Run the given routine and return the routine's output.

        '''
        self._controller.send_action('LArPix board',
                'run_routine', [name] + list(args))
        for _ in range(2):
            yield self._controller.receive(None)


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

    def data_rate(self, start_time, end_time, chip_or_channel):
        '''
        Return the data rate for the specified ASIC or channel between
        ``start_time`` and ``end_time``, as long as it's within the
        current run.

        '''
        self._controller.send_action('Run data', 'data_rate', [])
        for _ in range(2):
            yield self._controller.receive(None)

    def fetch_packets(self, start_time, end_time, chip_or_channel):
        '''
        Return all the packets produced by the specified ASIC or channel
        between ``start_time`` and ``end_time``, as long as they're from
        the current run.

        '''
        self._controller.send_action('Run data', 'packets', [])
        for _ in range(2):
            yield self._controller.receive(None)

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

