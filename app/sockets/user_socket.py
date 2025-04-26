from flask_socketio import emit, SocketIO
from flask import request
from app.controllers.user_controller import handle_data_controller, save_record_success_controller, save_record_failed_controller
from app.models.record import Record

socketio = SocketIO(cors_allowed_origins="*")
# 각 클라이언트 세션 저장하는 딕셔너리
clients = {}

# 운동 기록 저장 객체
record = Record()

LANDMARK_NAMES = [
    "코", "왼눈안", "왼눈", "왼눈밖", "오른눈안", "오른눈", "오른눈밖", "왼귀", "오른귀",
    "입술왼쪽", "입술오른쪽", "왼어깨", "오른어깨", "왼팔꿈치", "오른팔꿈치", "왼손목", "오른손목",
    "왼엄지", "오른엄지", "왼검지", "오른검지", "왼새끼", "오른새끼",
    "왼엉덩이", "오른엉덩이", "왼무릎", "오른무릎", "왼발목", "오른발목",
    "왼뒤꿈치", "오른뒤꿈치", "왼발끝", "오른발끝"
]

def register_user_socket(socketio):

    # 소켓 연결 후, 클라이언트로부터 받은 데이터들 Record 객체에 저장
    @socketio.on('connection')
    def handle_connect(data):
        phone_number = data.get('phoneNumber')
        # 처음 운동 시작 후 Record 객체에 데이터 저장
        record.exercise_name = data.get('exercise_name')
        record.exercise_weight = data.get('exercise_weight')
        record.exercise_cnt = data.get('exercise_cnt')
        record.phone_number = phone_number
        clients[phone_number] = request.sid
        print(f' 클라이언트 연결됨 : {phone_number} -> SID {request.sid}')

    # 운동 세트 다시 시작할 때
    @socketio.on('restart')
    def handle_reconnect(data):
        phone_number = data.get('phoneNumber')
        clients[phone_number] = request.sid
        print(f' 클라이언트 연결됨 : {phone_number} -> SID {request.sid}')

    # 소켓 연결 끊음
    # 신경 안 써도 될듯 이 부분.
    # @socketio.on('disconnection')
    # def handle_disconnect(data):
    #     print('클라이언트 연결 끊음')
    #     phone_number = data.get('phoneNumber')
    #     disconnected_sid = request.sid
    #     for phone_number, sid in list(clients.items()):
    #         if sid == disconnected_sid:
    #             del clients[phone_number]
    #             print(f'phone_number {phone_number} 연결 해제 처리 완료')
    #             break
        
    # 중간에 운동을 끊었을 때, 횟수는 현재 진행중인 service 계층에서의 cnt로 Record 객체를 업데이트하고 저장
    @socketio.on('exercise_disconnect')
    def handle_disconnect_exercise(data):
        phone_number = data.get('phoneNumber')
        removed = clients.pop(phone_number, None)
        # 중간에 운동 끊었을 때 지금까지 했던 운동 횟수에 DB에 저장하라고 호출
        # 2025/04/26 코멘트
        # 컨트롤러 함수에 넘겨주는 매개변수 record에서 사용자 이름, 운동 이름을 가져오고 운동횟수는 Service 계층에서 세고 있으니
        # Service 계층에서 cnt 변수 가져와서 DB에 저장하면 될듯.
        # ----------------------------------------------------
        save_record_failed_controller(record)
        if removed:
            print(f'🧹 연결 해제됨: {phone_number}')
        else:
            print(f'⚠️ 연결 정보 없음: {phone_number}')


    # 클라이언트 수동 연결 해제 요청 처리, 1세트 운동 성공적으로 끝났다는 의미이므로 DB에 Record 데이터 저장
    @socketio.on('disconnect_client')
    def handle_disconnect_client(data):
        phone_number = data.get('phoneNumber')
        removed = clients.pop(phone_number, None)
        # 1세트 운동 했을 때 성공적으로 저장
        save_record_success_controller(record)
        if removed:
            print(f'🧹 연결 해제됨: {phone_number}')
        else:
            print(f'⚠️ 연결 정보 없음: {phone_number}')

        
     # exercise_data로 데이터 넘겨받고 클라이언트로 반환
    # 요청 데이터로 phoneNumber, exerciseType, landmarks 정보는 필수
    # @socketio.on('exercise_data')
    # def handle_exercise_data(data):
    #     try:
    #         print(f"🏋 데이터 수신: {data}")
    #         result = handle_data_controller(data)
    #
    #         phone_number = data.get('phoneNumber')
    #         sid = clients.get(phone_number)
    #         if sid:
    #             print(f"📤 결과 전송 대상 SID: {sid}")
    #             socketio.emit('result', result, to=sid)
    #         else:
    #             print(f"⚠️ 클라이언트 SID를 찾을 수 없음: {phone_number}")
    #     except Exception as e:
    #         print(f"❌ 데이터 처리 중 예외 발생: {e}")
    #         emit('result', {'error': '서버 내부 오류가 발생했습니다.'})

    @socketio.on('exercise_data')
    def handle_exercise_data(data):
        try:
            phone_number = data.get('phoneNumber')

            # ❌ 연결되지 않은 사용자면 처리하지 않음
            if phone_number not in clients:
                return

            print(f"🏋 데이터 수신: {data}")

            for idx, point in enumerate(data.get('landmarks', [])):
                label = LANDMARK_NAMES[idx] if idx < len(LANDMARK_NAMES) else f"포인트 {idx}"
                print(f"{label:<8} [{idx:2d}]: x={point['x']}, y={point['y']}, z={point['z']}")


            result = handle_data_controller(data)

            sid = clients.get(phone_number)
            if sid:
                print(f"📤 결과 전송 대상 SID: {sid}")
                socketio.emit('result', result, to=sid)
            else:
                print(f"⚠️ 클라이언트 SID를 찾을 수 없음: {phone_number}")

        except Exception as e:
            print(f"❌ 데이터 처리 중 예외 발생: {e}")
            emit('result', {'error': '서버 내부 오류가 발생했습니다.'})

