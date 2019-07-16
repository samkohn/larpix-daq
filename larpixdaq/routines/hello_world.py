from larpixdaq.routines import Routine

def _hello_world(controller, send_data, send_info, *args):
    to_return = "Hello, %s!" % args
    send_info(to_return)
    return controller, to_return

hello_world = Routine('hello_world', _hello_world, ['name'])

registration = {'hello_world': hello_world}
