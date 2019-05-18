'''
Defines routines for different components.

'''

# from blah import my_script

class Routine(object):
    def __init__(self, name, func, params=None):
        if params is None:
            params = []
        self.name = name
        self.func = func
        self.params = params

def hello_world(controller, *args):
    to_return = "Hello, %s" % args
    return controller, to_return

producer_routines = {
        'hello': Routine('hello', hello_world, ['name']),
        'basic': Routine('basic', lambda board: (board, "Hi!")),
        }
