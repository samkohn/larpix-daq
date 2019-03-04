from webapp.app import create_app, socketio

app = create_app()
socketio.run(app)

