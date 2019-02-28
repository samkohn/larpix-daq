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
        self._controller = moddaq.Controller(
            core_address='tcp://127.0.0.1:5550',
            response_address='tcp://127.0.0.1:5551'
        )

    def close(self):
        self._controller.cleanup()


    def process_incoming_messages(self):
        '''
        Read through messages received from the Core and update members
        accordingly.

        '''
        again = True
        while again:
            messages = self._controller.receive()
            again = bool(messages)
            if again:
                for message in messages:
                    self._controller.handle(message)

    ### Configurations

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
        action_id = self._controller.send_action('LArPix board',
                'run_routine', [name] + list(args))
        return action_id


    ### Physics runs

    def begin_physics_run(self):
        '''
        Begin taking physics data, activate online data monitoring and
        analytics, and store the data in offline storage.

        '''
        self._controller.request_state_change('RUN')
        action_id = self._controller.send_action('LArPix board',
                'begin_run', [])
        return action_id

    def end_physics_run(self):
        '''
        Stop taking physics data, deactivate online data monitoring and
        analytics, and finalize the offline storage.

        '''
        action_id = self._controller.send_action('LArPix board',
                'end_run', [])
        self._controller.request_state_change('READY')
        return action_id

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
        action_id = self._controller.send_action('Run data',
                'data_rate', [])
        return action_id

    def fetch_packets(self, start_time, end_time, chip_or_channel):
        '''
        Return all the packets produced by the specified ASIC or channel
        between ``start_time`` and ``end_time``, as long as they're from
        the current run.

        '''
        action_id = self._controller.send_action('Run data', 'packets', [])
        return action_id

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

