'''
Manage connection to the DAQ Core via Controller objects.

'''

from flask import current_app, g
from larpixdaq.operator import Operator

def get_daq():
    if 'daq' not in g:
        daq = Operator()
        while daq._controller.addresses is None:
            daq.process_incoming_messages()
        g.daq = daq
    return g.daq

def close_daq(e=None):
    daq = g.pop('daq', None)
    if daq is not None:
        daq.close()

def init_app(app):
    app.teardown_appcontext(close_daq)

