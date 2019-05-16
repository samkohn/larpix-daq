'''
Manage connection to the DAQ Core via Controller objects.

'''

from flask import current_app, g
from larpixdaq.operator import Operator

def get_daq(address):
    if 'daq' not in g:
        daq = Operator(address)
        g.daq = daq
    return g.daq

def close_daq(e=None):
    daq = g.pop('daq', None)

def init_app(app):
    app.teardown_appcontext(close_daq)

