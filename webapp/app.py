'''
Webapp for LArPixDAQ.

'''
import json
import logging

from flask import Flask, render_template, current_app

from webapp.daq import get_daq
from flask_socketio import SocketIO, emit

socketio = SocketIO()
bg_thread = None

def create_app():
    app = Flask(__name__)

    @app.route('/')
    def hello():
        return render_template('index.html')

    @socketio.on('connect')
    def start_bg_thread():
        global bg_thread
        if bg_thread is None:
            daq = get_daq()
            socketio.start_background_task(bg_task, daq)

    def simple_daq(method_name, msg):
        daq = get_daq()
        method = getattr(daq, method_name)
        result = method()
        result['id'] = msg['id']
        logging.debug(result)
        emit('action-update', result)

    def generator_daq(method_name, msg):
        daq = get_daq()
        method = getattr(daq, method_name)
        for result in method(*msg['params']):
            logging.debug(result)
            result['id'] = msg['id']
            emit('action-update', result)

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
        generator_daq('data_rate', msg)

    @socketio.on('command/packets')
    def end_run(msg):
        msg['params'] = [0, 0, 0]
        generator_daq('fetch_packets', msg)

    @socketio.on('command/run_routine')
    def run_routine(msg):
        daq = get_daq()
        result_id = msg[0]
        routine = msg[1]
        routine_name = routine['name']
        num_params = routine['num_params']
        params = msg[2][:num_params]
        for result in daq.run_routine(routine_name, *params):
            logging.debug(result)
            result['id'] = result_id
            emit('action-update', result)

    @socketio.on('command/configure_chip')
    def configure_chip(msg):
        generator_daq('configure_chip', msg)

    @socketio.on('command/write_config')
    def configure_chip(msg):
        generator_daq('write_configuration', msg)

    @socketio.on('command/verify_config')
    def verify_config(msg):
        generator_daq('validate_configuration', msg)

    @socketio.on('command/retrieve_config')
    def retrieve_config(msg):
        generator_daq('retrieve_configuration', msg)

    @app.route('/command/actionid/<actionid>')
    def get_action_id(actionid):
        o = get_daq()
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

def bg_task(daq):
    while True:
        daq._controller.request_clients()
        result = daq._controller.receive(None)
        socketio.emit('client-update', result)
        daq._controller.request_state()
        result = daq._controller.receive(None)
        socketio.emit('state-update', result)
        socketio.sleep(0.5)

