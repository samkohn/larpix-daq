'''
Webapp for LArPixDAQ.

'''
import json

from flask import Flask, render_template, current_app

from larpixdaq.operator import Operator

def create_app():
    app = Flask(__name__)

    @app.before_first_request
    def init_operator():
        app.config['OPERATOR'] = Operator()

    @app.route('/')
    def hello():
        return render_template('index.html')

    @app.route('/command/start-run', methods=['POST'])
    def start_run():
        current_app.config['OPERATOR'].begin_physics_run()
        return 'nothing'

    @app.route('/command/end-run', methods=['POST'])
    def end_run():
        actionid = current_app.config['OPERATOR'].end_physics_run()
        return str(actionid)

    @app.route('/command/process', methods=['POST'])
    def process_messages():
        current_app.config['OPERATOR'].process_incoming_messages()
        return 'nothing'

    @app.route('/command/actionid/<actionid>')
    def get_action_id(actionid):
        o = current_app.config['OPERATOR']
        try:
            result = o.retrieve_result(int(actionid))
        except:
            result = 'invalid id'
        return json.dumps(result)


    return app

