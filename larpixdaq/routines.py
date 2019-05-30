'''
Defines routines for different components.

'''

# from blah import my_script

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

def hello_world(controller, send_data, send_info, *args):
    to_return = "Hello, %s" % args
    send_info(to_return)
    return controller, to_return

producer_routines = {
        'hello': Routine('hello', hello_world, ['name']),
        }
