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

    @socketio.on('command/start-run')
    def start_run(msg):
        daq = get_daq()
        result = daq.begin_physics_run()
        logging.debug(result)
        return json.dumps(result)

    @socketio.on('command/end-run')
    def end_run(msg):
        daq = get_daq()
        result = daq.end_physics_run()
        logging.debug(result)
        return json.dumps(result)

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

