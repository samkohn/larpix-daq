'''
Defines routines for different components.

'''

# from blah import my_script

class Routine(object):
    def __init__(self, name, func, num_params, params=None):
        if num_params == 0:
            params = []
        self.name = name
        self.func = func
        self.num_params = num_params
        self.params = params

def hello_world(controller, *args):
    to_return = "Hello, %s" % args
    return controller, to_return

producer_routines = {
        'hello': Routine('hello', hello_world, 1, ['name']),
        }
