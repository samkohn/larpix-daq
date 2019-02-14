'''
The operator interface for the LArPix DAQ system.

'''

class Operator(object):
    '''
    The Operator class handles all of the needs of an DAQ operator:
    start/end runs, load/validate configurations, run calibrations,
    examine data samples and data rates, etc.

    '''

    def __init__(self):
        self.chips = None
        self.geometry = None
        self.run_number = 0
        self.is_running = False
        self.routines = []
        self.configurations = []


    ### Configurations

    def load_configuration(self, name):
        '''
        Load the given configuration onto the LArPix ASICs.

        '''
        pass

    def validate_configuration(self):
        '''
        Read the configuration from all of the LArPix ASICs and return
        ``True`` if the actual values match those stored in software.

        '''
        pass

    def learn_configuration(self):
        '''
        Read the configuration from all of the LArPix ASICs and store
        the actual values in software, replacing the existing values.

        '''
        pass

    def fetch_configurations(self):
        '''
        Return a list of available configurations.

        '''
        pass


    ### Calibrations

    def list_routines(self):
        '''
        Return a list of routines/calibrations.

        '''
        pass

    def run_routine(self, name):
        '''
        Run the given routine and return the routine's output.

        '''
        pass


    ### Physics runs

    def begin_physics_run(self):
        '''
        Begin taking physics data, activate online data monitoring and
        analytics, and store the data in offline storage.

        '''
        pass

    def end_physics_run(self):
        '''
        Stop taking physics data, deactivate online data monitoring and
        analytics, and finalize the offline storage.

        '''
        pass

    def data_rate(self, start_time, end_time, chip_or_channel):
        '''
        Return the data rate for the specified ASIC or channel between
        ``start_time`` and ``end_time``, as long as it's within the
        current run.

        '''
        pass

    def fetch_packets(self, start_time, end_time, chip_or_channel):
        '''
        Return all the packets produced by the specified ASIC or channel
        between ``start_time`` and ``end_time``, as long as they're from
        the current run.

        '''
        pass

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

