from flask_socketio import emit
from flask import request
from app.controllers.user_controller import handle_data_controller

# 각 클라이언트 세션 저장하는 딕셔너리
clients = {}

def register_user_socket(socketio):

    # 소켓 연결
    @socketio.on('connection')
    def handle_connect(data):
        print('클라이언트 연결됨')
        phone_number = data.get('phone_number')
        clients[phone_number] = request.sid

    # 소켓 연결 끊음
    # 신경 안 써도 될듯 이 부분.
    @socketio.on('disconnection')
    def handle_disconnect(data):
        print('클라이언트 연결 끊음')
        phone_number = data.get('phone_number')
        disconnected_sid = request.sid
        for phone_number, sid in list(clients.items()):
            if sid == disconnected_sid:
                del clients[phone_number]
                print(f'phone_number {phone_number} 연결 해제 처리 완료')
                break
        
# 데이터를 하나의 클라이언트에게 전송
# original_data => 원본 데이터, revised_data => 운동 자세 교정 데이터
def send_data(original_data, revised_data,  socketio):
    result = {
        "original": original_data,
        "revised": revised_data
    }
    socketio.emit('result', result)
    
