from flask import Flask
from flask_socketio import SocketIO
from app.sockets.user_socket import register_user_socket

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')

register_user_socket(socketio)

if __name__ == '__main__':
    socketio.run(app, debug=True)