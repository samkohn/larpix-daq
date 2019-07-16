'''
The operator interface for the LArPix DAQ system.

'''
import xylem

end_receive_loop_headers = {
        'ACTIONS',
        'ACTION RESULT',
        'STATE',
        'STATE REQUEST',
        'CLIENTS',
        }

class Operator(object):
    """The LArPix DAQ Operator module provides the interface into the
    DAQ core for all DAQ operations.

    The Operator class handles all of the needs of an DAQ operator:
    start/end runs, load/validate configurations, run calibrations,
    examine data samples and data rates, etc.

    Operator methods interact with the DAQ Core to accomplish the
    desired behavior. The DAQ Core can send
    multiple responses for a single request - e.g. an immediate
    acknowledgement of receipt and then the eventual result. The
    methods implementing these interactions return generator
    iterators <https://docs.python.org/3/glossary.html#term-generator>
    rather than values. The way to call these functions usually looks
    like::

        o = Operator()
        final_responses = []
        for response in o.run_routine('example'):
            print(response)
            # interact with response object within loop
        # When the loop ends, the last response received is still saved in
        # the response object
        final_responses.append(response)

    :param address: the TCP address of the DAQ Core. The port will be
        added automatically. (Optional, if omitted or ``None``, will
        default to ``tcp://127.0.0.1``.)
    """

    def __init__(self, address=None):
        if address is None:
            address = 'tcp://127.0.0.1:5551'
        else:
            address += ':5551'
        self.chips = None
        self.geometry = None
        self.run_number = 0
        self.is_running = False
        self.routines = []
        self.configurations = {}
        self._controller = xylem.Controller(address)

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

    def retrieve_pixel_layout(self, filename, timeout=None):
        self._controller.send_action('Online monitor', 'retrieve_pixel_layout',
                [filename])
        for result in self._receive_loop(timeout):
            yield result

    def load_pixel_layout(self, filename, timeout=None):
        self._controller.send_action('Online monitor', 'load_pixel_layout',
                [filename])
        for result in self._receive_loop(timeout):
            yield result

    ### Configurations

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

    def validate_configuration(self, chip, timeout=None):
        '''
        Read the configuration from the specified LArPix ASIC and return
        ``(True/False, {name: (actual, stored)})``.

        '''
        self._controller.send_action('LArPix board', 'validate_config',
                [chip])
        for result in self._receive_loop(timeout):
            yield result

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

    def prepare_physics_run(self, timeout=None):
        '''
        Enter the "READY" DAQ state so that all DAQ components are ready
        to begin the physics run.

        '''
        self._controller.request_state_change('READY')
        for result in self._receive_loop(timeout):
            yield result

    def begin_physics_run(self, timeout=None):
        '''
        Begin taking physics data, activate online data monitoring and
        analytics, and store the data in offline storage.

        '''
        self._controller.request_state_change('RUN')
        for result in self._receive_loop(timeout):
            yield result


    def end_physics_run(self, timeout=None):
        '''
        Stop taking physics data, deactivate online data monitoring and
        analytics, and finalize the offline storage.

        '''
        self._controller.request_state_change('STOP')
        for result in self._receive_loop(timeout):
            yield result

