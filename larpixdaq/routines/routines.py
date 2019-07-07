'''
Defines routines for different components.

'''
import importlib
import os
import sys

ROUTINES = {}
_routine_files = {}

def init_routines(location=None):
    if location is None:
        location = os.path.dirname(__file__)
    if location not in sys.path:
        sys.path.insert(0, location)
    importlib.invalidate_caches()
    routine_files = [os.path.splitext(x)[0] for x in os.listdir(location) if (
        x.endswith('.py') and x != __file__)]
    for routine_file in routine_files:
        if routine_file in _routine_files:
            module_old = _routine_files[routine_file]
            module = importlib.reload(module_old)
        else:
            module = importlib.import_module(routine_file)
        _routine_files[routine_file] = module
        if hasattr(module, 'registration'):
            ROUTINES.update(module.registration)
    print(ROUTINES)

class Routine(object):
    '''
    Represents a routine run using the LArPix Control board.

    Routine functions are passed three arguments for the purpose of
    interacting with the LArPix-control and DAQ systems, so they should
    have the following signature:

    ```
    def func(controller, send_data, send_info, [...])
    ```

    - ``controller`` is the current instance of the LArPix-control
      Controller object
    - ``send_data`` is a function which sends data to the DAQ pipeline.
      The first argument is the data, in bytes. The second is optional
      and is a dict with metadata. Default metadata of Unix timestamp
      and component name is automatically added to the supplied dict.
    - ``send_info`` is a function which sends an informational message
      to the DAQ pipeline. The first and only argument is the message as
      a string.
    - Any other arguments must be listed in order in self.params.

    '''
    def __init__(self, name, func, params=None):
        if params is None:
            params = []
        self.name = name
        self.func = func
        self.params = params

