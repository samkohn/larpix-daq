'''
Webapp for LArPixDAQ.

'''
import json
import os
os.environ['EVENTLET'] = "yes"

from flask import Flask, render_template, current_app, request

from webapp.daq import get_daq
from flask_socketio import SocketIO, emit

socketio = SocketIO(async_mode='eventlet')
address = None

def create_app():
    app = Flask(__name__)

    @app.route('/')
    def hello():
        return render_template('index.html')

    @app.route('/state', methods=['GET', 'POST'])
    def state():
        if request.method == 'GET':
            daq = get_daq(address)
            daq._controller.request_state()
            result = daq._controller.receive(None)
            return json.dumps(result)
        else:
            newstate = request.get_json()['new']
            oldstate = request.get_json()['old']
            result = {'message': {'result': newstate}}
            socketio.emit('state-update', result)
            return ('', 204)

    @app.route('/component', methods=['GET', 'POST', 'DELETE'])
    def component():
        if request.method == 'GET':
            daq = get_daq(address)
            daq._controller.request_clients()
            result = daq._controller.receive(None)
            return json.dumps(result)
        elif request.method == 'POST':
            newclient = request.get_json()['new']
            allclients = request.get_json()['all']
            result = {'message': {'result': allclients}}
            socketio.emit('client-update', result)
            return ('', 204)
        elif request.method == 'DELETE':
            lostclient = request.get_json()['lost']
            allclients = request.get_json()['all']
            result = {'message': {'result': allclients}}
            socketio.emit('client-update', result)
            return ('', 204)

    @app.route('/packets', methods=['POST'])
    def packets():
        result = {
                'packets': request.get_json()
                }
        socketio.emit('data-update', result)
        return ('', 204)

    @app.route('/boards', methods=['GET', 'POST'])
    def boards():
        if request.method == 'GET':
            daq = get_daq(address)
            for result in daq.get_boards():
                pass
            retrieved = result['message']['result']
            return json.dumps(retrieved)
        elif request.method == 'POST':
            daq = get_daq(address)
            filename = request.get_json()['filename']
            if request.get_json()['shortname']:
                filename = 'controller/' + filename + '_chip_info.json'
            for result in daq.load_board(filename):
                pass
            return ('', 204)

    def simple_daq(method_name, msg):
        daq = get_daq(address)
        method = getattr(daq, method_name)
        result = method()
        result['id'] = msg['id']
        result['display'] = msg['display']
        current_app.logger.debug(result)
        emit('action-update', result)

    def run_in_background(target, *args, **kwargs):
        socketio.start_background_task(target,
                current_app._get_current_object(), *args,
                **kwargs)

    def generator_daq(app, method_name, msg):
        with app.app_context():
            daq = get_daq(address)
            method = getattr(daq, method_name)
            for result in method(*msg['params'], timeout=None):
                app.logger.debug(result)
                if result is None:
                    result = {
                            'id': msg['id'],
                            'display': msg['display'],
                            'message': {
                                'result': 'ERROR: timed out',
                                },
                            }
                result['id'] = msg['id']
                result['display'] = msg['display']
                app.logger.debug('emitting result: %s', result)
                socketio.emit('action-update', result)
                yield_to_socketio(socketio)

    @socketio.on('command/prepare-run')
    def prepare_run(msg):
        simple_daq('prepare_physics_run', msg)

    @socketio.on('command/start-run')
    def start_run(msg):
        simple_daq('begin_physics_run', msg)

    @socketio.on('command/end-run')
    def end_run(msg):
        simple_daq('end_physics_run', msg)

    @socketio.on('command/data-rate')
    def end_run(msg):
        msg['params'] = [0, 0, 0]
        run_in_background(generator_daq, 'data_rate', msg)

    @socketio.on('command/packets')
    def end_run(msg):
        msg['params'] = [0, 0, 0]
        run_in_background(generator_daq, 'fetch_packets', msg)

    @socketio.on('command/messages')
    def end_run(msg):
        run_in_background(generator_daq, 'fetch_messages', msg)

    @socketio.on('command/run_routine')
    def run_routine(msg):
        run_in_background(generator_daq, 'run_routine', msg)

    @socketio.on('command/configure_chip')
    def configure_chip(msg):
        run_in_background(generator_daq, 'configure_chip', msg)

    @socketio.on('command/write_config')
    def configure_chip(msg):
        run_in_background(generator_daq, 'write_configuration', msg)

    @socketio.on('command/verify_config')
    def verify_config(msg):
        run_in_background(generator_daq, 'validate_configuration', msg)

    @socketio.on('command/retrieve_config')
    def retrieve_config(msg):
        run_in_background(generator_daq, 'retrieve_configuration', msg)

    @socketio.on('command/send_config')
    def send_config(msg):
        run_in_background(generator_daq, 'send_configuration', msg)

    @socketio.on('command/read_config')
    def read_config(msg):
        run_in_background(generator_daq, 'read_configuration', msg)

    @app.route('/routines')
    def get_routines():
        o = get_daq(address)
        for result in o.list_routines():
            pass
        app.logger.debug(result)
        return json.dumps(result)

    @app.route('/command/actionid/<actionid>')
    def get_action_id(actionid):
        o = get_daq(address)
        try:
            result = o.retrieve_result(int(actionid))
        except:
            result = 'invalid id'
        return json.dumps(result)

    @socketio.on('message')
    def test(message):
        print(message)
        emit('/', 'Hello, %s!' % message)


    from . import daq
    daq.init_app(app)

    socketio.init_app(app)

    return app

def yield_to_socketio(socketio):
    '''
    Momentarily yield to the socketio/server process.

    This is necessary to send multiple spaced-out socketio messages in a
    long-running (i.e. blocking) method. Without this, the socketio
    server never gets a chance to send the intermediary messages.

    '''
    socketio.sleep(0)

