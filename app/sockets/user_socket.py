from flask_socketio import emit
from app.controllers.user_controller import handle_data_controller

def register_user_socket(socketio):
    
    @socketio.on('test')
    def on_get_user(data):
        result = handle_data_controller(data)
        emit('result', result)