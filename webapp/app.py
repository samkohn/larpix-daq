'''
Webapp for LArPixDAQ.

'''
import json

from flask import Flask, render_template, current_app

from .daq import get_daq

def create_app():
    app = Flask(__name__)

    @app.route('/')
    def hello():
        return render_template('index.html')

    @app.route('/command/start-run', methods=['POST'])
    def start_run():
        daq = get_daq()
        action_id = daq.begin_physics_run()
        print(action_id)
        return 'nothing'

    @app.route('/command/end-run', methods=['POST'])
    def end_run():
        daq = get_daq()
        daq.end_physics_run()
        return 'nothing'

    @app.route('/command/process', methods=['POST'])
    def process_messages():
        daq = get_daq()
        daq.process_incoming_messages()
        return 'nothing'

    @app.route('/command/actionid/<actionid>')
    def get_action_id(actionid):
        o = get_daq()
        try:
            result = o.retrieve_result(int(actionid))
        except:
            result = 'invalid id'
        return json.dumps(result)

    from . import daq
    daq.init_app(app)

    return app

