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
        phone_number = data.get('phoneNumber')
        clients[phone_number] = request.sid

    # 소켓 연결 끊음
    # 신경 안 써도 될듯 이 부분.
    @socketio.on('disconnection')
    def handle_disconnect(data):
        print('클라이언트 연결 끊음')
        phone_number = data.get('phoneNumber')
        disconnected_sid = request.sid
        for phone_number, sid in list(clients.items()):
            if sid == disconnected_sid:
                del clients[phone_number]
                print(f'phone_number {phone_number} 연결 해제 처리 완료')
                break
        
     # exercise_data로 데이터 넘겨받고 클라이언트로 반환
    # 요청 데이터로 phoneNumber, exerciseType, landmarks 정보는 필수
    @socketio.on('exercise_data')
    def handle_exercise_data(data):
        try:
            print(f"🏋 데이터 수신: {data}")
            result = handle_data_controller(data)

            phone_number = data.get('phoneNumber')
            sid = clients.get(phone_number)
            if sid:
                print(f"📤 결과 전송 대상 SID: {sid}")
                socketio.emit('result', result, to=sid)
            else:
                print(f"⚠️ 클라이언트 SID를 찾을 수 없음: {phone_number}")
        except Exception as e:
            print(f"❌ 데이터 처리 중 예외 발생: {e}")
            emit('result', {'error': '서버 내부 오류가 발생했습니다.'})
    
