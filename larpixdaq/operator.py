'''
The operator interface for the LArPix DAQ system.

'''
import xylem

from larpixdaq.core import CORE_PORT

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

    Each method has an optional keyword parameter ``timeout``. If
    omitted (or if ``None``), then the Operator will wait forever for a
    response from the DAQ Core. If ``timeout`` is provided, then the
    Operator will yield ``None`` as an indication of an error after a
    maximum wait of 10 times the given timeout, in seconds.

    .. note:: if the timeout limit is reached and the "missing" message
        arrives later, it will be confused with future results.
        Operator objects do not maintain useful internal state, so it is
        acceptable (and recommended!) to initialize a new Operator if
        the current Operator ran into a timeout issue.

    :param address: the TCP address of the DAQ Core. The port will be
        added automatically. (Optional, if omitted or ``None``, will
        default to ``tcp://127.0.0.1``.)
    """

    def __init__(self, address=None):
        if address is None:
            address = 'tcp://127.0.0.1:%d' % CORE_PORT
        else:
            address += ':%d' % CORE_PORT
        self._controller = xylem.Controller(address)

    def cleanup(self):
        """Clean up the ZMQ objects used in the Operator.

        Only necessary if you are initializing and destroying multiple
        Operators in one session.
        """
        self._controller.cleanup()

    def _receive_loop(self, timeout=None):
        """Loop through receiving incoming messages, up to a timeout.

        The loop terminates if either:
        - the message header is one of the selected "end transmission"
          headers listed in this module's ``end_receive_loop_headers``
          list, or
        - 10 calls to receive have been made (and possibly timed-out)
        """
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
        """Get a list of board (PCB) names available to load."""
        self._controller.send_action('LArPix board', 'get_boards', [])
        for result in self._receive_loop(timeout):
            yield result

    def load_board(self, filename, timeout=None):
        """Load the particular board (PCB) into LArPix Control as a
        ``Controller`` configuration.

        :param filename: the file to load, e.g.
            ``'controller/pcb-1_chip_info.json'``
        """
        self._controller.send_action('LArPix board', 'load_board',
                [filename])
        for result in self._receive_loop(timeout):
            yield result

    def retrieve_pixel_layout(self, timeout=None):
        """Fetch the currently-loaded pixel geometry layout."""
        self._controller.send_action('Online monitor', 'retrieve_pixel_layout',
                [])
        for result in self._receive_loop(timeout):
            yield result

    def load_pixel_layout(self, pcb_id, timeout=None):
        """Load the specified pixel layout into the online monitor.

        :param pcb_id: the PCB specifier to request from
            ``larpix.configs.load``, e.g. ``pcb-3``.
        """
        self._controller.send_action('Online monitor', 'load_pixel_layout',
                [pcb_id])
        for result in self._receive_loop(timeout):
            yield result

    ### Configurations

    def write_configuration(self, chip, timeout=None):
        """Send the configuration values from software onto the ASIC.

        :param chip: the chip key as a string
        """
        self._controller.send_action('LArPix board', 'write_config',
                [chip])
        for result in self._receive_loop(timeout):
            yield result

    def read_configuration(self, chip, timeout=None):
        """Read the configuration values from the ASIC.

        :param chip: the chip key as a string
        """
        self._controller.send_action('LArPix board', 'read_config',
                [chip])
        for result in self._receive_loop(timeout):
            yield result

    def validate_configuration(self, chip, timeout=None):
        """Read the configuration from the specified LArPix ASIC and return
        ``(True/False, {name: (actual, stored)})``.

        :param chip: the chip key as a string
        """
        self._controller.send_action('LArPix board', 'validate_config',
                [chip])
        for result in self._receive_loop(timeout):
            yield result

    def retrieve_configuration(self, chip, timeout=None):
        """Return a dict of the current configuration stored in software
        for the given chipid.

        :param chip: the chip key as a string
        :returns: a dict mapping the configuration item name (could be
            multiple or part of a register) to the value.
        """
        self._controller.send_action('LArPix board', 'retrieve_config',
                [chip])
        for result in self._receive_loop():
            yield result

    def send_configuration(self, updates, timeout=None):
        """Send the given configuration updates to the LArPix control
        software.

        :param updates: a dict mapping chip keys to a dict readable by
            the LArPix Control ``Configuration.from_dict``. Note that
            omitted registers will not be updated (but also will not be
            deleted or reset).
        """
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

    def load_routines(self, location):
        """Load any routines saved at ``location`` into the
        LArPix Producer.

        :param location: the directory containing the routines files to
            load.
        :returns: the new list of routines (same as subsequently calling
            ``list_routines``)
        """
        self._controller.send_action('LArPix board', 'load_routines',
                [location])
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

