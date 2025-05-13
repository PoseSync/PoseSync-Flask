import math

from flask_socketio import emit, SocketIO, disconnect
from flask import request
from app.controllers.user_controller import handle_data_controller, save_record_success_controller, save_record_failed_controller
from app.models.record import Record
from app.util.calculate_landmark_distance import connections, calculate_named_linked_distances, \
    map_distances_to_named_keys, bone_name_map
from app.util.pose_landmark_enum import PoseLandmark   # id→공식명 enum
import time
from app.util.pose_transform import process_pose_landmarks, reverse_pose_landmarks

from collections import deque
import time
import numpy as np

# AI 모델 가져오기
from app.ai.ai_model import fall_model

# 가속도 계산
from app.util.calculate_landmark_accerlation import calculate_acceleration

# 전화 걸기
from app.util.call import call_user

socketio = SocketIO(cors_allowed_origins="*")
# 각 클라이언트 세션 저장하는 딕셔너리
clients = {}

# 시퀀스 버퍼 (60프레임)
accel_seq_buffer = deque(maxlen=30)

fall_detected = False

# 테스트 모드 전역 변수
TEST_OFFSET_ENABLED = False  # 테스트 모드 활성화

# 운동 기록 객체 저장 리스트
# 운동 한 세트 끝낼때마다 맨 앞에 있는 요소 삭제
record_list = []

# 현재 클라이언트로 전달받은 데이터가 맨 처음 데이터인지 확인 => 이는 초기 유저 landmark의 점과 점 사이의 거리를 구하기 위함
is_first = True

# 유저의 각 landmark 사이의 거리
distances = {}

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
        record = Record()
        # 처음 운동 시작 후 Record 객체에 데이터 저장
        record.exercise_name = data.get('exercise_name')
        record.exercise_weight = data.get('exercise_weight')
        record.exercise_cnt = data.get('exercise_cnt')
        record.phone_number = phone_number
        # 생성된 Record 객체 record_list에 저장
        record_list.append(record)
        clients[phone_number] = request.sid
        global is_first
        is_first = True #첫 서버연결 때 운동 패킷 첫 연결여부 True
        print(f' 클라이언트 연결됨 : {phone_number} -> SID {request.sid}')

    # 운동 세트 시작할 때
    @socketio.on('restart')
    def handle_reconnect(data):
        phone_number = data.get('phoneNumber')
        clients[phone_number] = request.sid

        # 운동 세트 시작할 때 운동 횟수, 이름 보내줌.
        socketio.emit('start', {
            "exercise_name": record_list[0].exercise_name,
            "exercise_weight": record_list[0].exercise_weight
        },
        to=request.sid
        )
        print(f' 클라이언트 연결됨 : {phone_number} -> SID {request.sid}')

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
                reset_globals()
                print(f'phone_number {phone_number} 연결 해제 처리 완료')
                break
        
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
        save_record_failed_controller(record_list[0])
        # 운동 중이던 세트 삭제
        del record_list[0]
        # 다음 운동 정보 전송
        socketio.emit('next',
                      {
                          "exercise_name": record_list[0].exercise_name,
                          "exercise_cnt": record_list[0].exercise_cnt,
                          "exercise_weight": record_list[0].exercise_weight
                      },
                      to=removed
                      )
        if removed:
            disconnect(sid=removed)
            # 전역변수 초기화
            reset_globals()
            print(f'🧹 연결 해제됨: {phone_number}')
        else:
            print(f'⚠️ 연결 정보 없음: {phone_number}')


    # 클라이언트 수동 연결 해제 요청 처리, 1세트 운동 성공적으로 끝났다는 의미이므로 DB에 Record 데이터 저장
    @socketio.on('disconnect_client')
    def handle_disconnect_client(data):
        global is_first, distances
        phone_number = data.get('phoneNumber')
        removed = clients.pop(phone_number, None)
        # 1세트 운동 했을 때 성공적으로 저장
        save_record_success_controller(record_list[0])
        # 원래 했던 운동 record_list에서 삭제
        del record_list[0]

        # 다음 운동 정보 전송, record_list가 비어있지 않은 경우에만 전송
        if record_list:
            socketio.emit('next', {
                "exercise_name": record_list[0].exercise_name,
                "exercise_cnt": record_list[0].exercise_cnt,
                "exercise_weight": record_list[0].exercise_weight
            }, to=removed)
        if removed:
            # 다음 세트 시작 시 다시 각 landmark 사이의 거리를 구하기 위해서 is_first 값 변경
            is_first = True
            distances = {}

            # 소켓 연결 끊음.
            disconnect(sid=removed)
            # 전역변수 초기화
            reset_globals()
            print(f'🧹 연결 해제됨: {phone_number}')
        else:
            print(f'⚠️ 연결 정보 없음: {phone_number}')

    @socketio.on('exercise_data')
    def handle_exercise_data(data):
        global is_first, distances, fall_detected
        start_time = time.perf_counter()
        try:
            # 클라이언트에서 받은 원본 랜드마크 데이터
            landmarks = data.get('landmarks', [])

            fall = False

            print(f'클라이언트에서 받자마자 => {landmarks}')

            # 1. 가속도 계산 및 시퀀스 버퍼에 누적
            acceleration = calculate_acceleration(landmarks)
            if acceleration:
                # head와 pelvis의 평균 가속도를 [x, y, z]
                vec = acceleration["head_acceleration"] + acceleration["pelvis_acceleration"]
                accel_seq_buffer.append(vec)

                print(f"[{time.time()}] ✅ accel 추가됨, 현재 길이: {len(accel_seq_buffer)}")

                # 버퍼가 60개 이상일 때 매 프레임마다 예측 수행
                if len(accel_seq_buffer) >= 30:
                    model_input = np.array(list(accel_seq_buffer)[-30:]).reshape(1, 30, 6)
                    prediction = fall_model.predict(model_input, verbose=0)
                    # 임계값 0.8로 수정해서 낙상 감지 기준을 더 빡빡하게
                    fall = bool(prediction[0][0] > 111.0)
                    print(f"예측값: {prediction[0][0]}")
                    if fall and not fall_detected:
                        print("##########  낙상 감지 ##########")
                        fall_detected = True
                        # 전화 걸기
                        call_user()


            # id → name 필드 보강
            for lm in data['landmarks']:
                lm['name'] = PoseLandmark(lm['id']).name


            # 처음 데이터 통신할 때 뼈 길이 계산
            if is_first:
                is_first = False

                # 뼈 길이 계산
                distances = calculate_named_linked_distances(  # 뼈 길이
                    data['landmarks'], connections
                )
                distances = map_distances_to_named_keys(distances, bone_name_map)
                print(f"뼈 길이 : {distances}")
            #--------------------------------------------------------------------------------------

            # 사람 중심 좌표계로 변환 및 정규화
            transformed_landmarks, transform_data = process_pose_landmarks(landmarks)



            # 변환된 랜드마크로
            data['landmarks'] = transformed_landmarks
            data['__transformData'] = transform_data

            # 서버 내부에서 사용할 수 있도록 뼈 길이 데이터 추가
            data["bone_lengths"] = distances

            # requestId 추출
            request_id = data.get('requestId')
            phone_number = data.get('phoneNumber')

            # 연결되지 않은 사용자면 처리하지 않음
            if phone_number not in clients:
                return

            # 컨트롤러에서 데이터 처리 (가이드라인 생성)
            result = handle_data_controller(data)

            # 가이드라인 랜드마크를 시각화를 위해 원본 좌표계로 역변환
            visualization_landmarks = reverse_pose_landmarks(
                result['landmarks'],
                transform_data
            )

            # 시각화용 랜드마크 추가하고 원본 제거
            result['visualizationLandmarks'] = visualization_landmarks


            print('⭕')

            # 레이턴시 측정
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            result['latency'] = round(elapsed_ms, 2)

            print('♥❌')

            # 중요: requestId를 결과에 포함
            result['requestId'] = request_id

            # 낙상여부를 반환 데이터에 추가, true/false 값
            result['is_fall'] = fall

            # 클라이언트에서 사용하지 않는 데이터 바로 삭제
            del result['landmarks']  # 원본 변환 랜드마크 제거 (네트워크 부하 감소)
            del result['__transformData']  # 변환 데이터 삭제
            del result['bone_lengths']  # 뼈 길이 데이터 삭제

            # 결과 전송
            sid = clients.get(phone_number)
            if sid:

                print(f'클라이언트에게 전송 => {result}')

                socketio.emit('result', result, to=sid)
            else:
                print(f"⚠️ 클라이언트 SID를 찾을 수 없음: {phone_number}")

        except Exception as e:
            print(f"❌ 데이터 처리 중 예외 발생: {e}")
            import traceback
            traceback.print_exc()
            emit('result', {'error': '서버 내부 오류가 발생했습니다.'})


# 테스트 메서드
##########################################################################################################

# 1. 기본 오프셋 테스트
def apply_test_offset_basic(result):
    """모든 랜드마크에 일정한 오프셋 적용"""
    if 'landmarks' in result:
        for landmark in result['landmarks']:
            landmark['x'] += 0.2  # 오른쪽으로 이동
            landmark['y'] += 0.1  # 아래로 이동


# 2. 파동 패턴 테스트
def apply_test_offset_wave(result):
    """파동 패턴으로 랜드마크 이동 (더 확실한 시각적 차이)"""
    if 'landmarks' in result:
        for idx, landmark in enumerate(result['landmarks']):
            # 사인파 패턴으로 x, y 오프셋
            offset_x = 0.15 * math.sin(idx * 0.5)
            offset_y = 0.1 * math.cos(idx * 0.5)
            landmark['x'] += offset_x
            landmark['y'] += offset_y


# 3. 특정 관절 확대 테스트
def apply_test_offset_joints(result):
    """주요 관절만 크게 이동"""
    if 'landmarks' in result:
        key_joints = {
            11: (0.3, 0.0),  # 왼쪽 어깨
            12: (-0.3, 0.0),  # 오른쪽 어깨
            13: (0.4, 0.2),  # 왼쪽 팔꿈치
            14: (-0.4, 0.2),  # 오른쪽 팔꿈치
            15: (0.5, 0.3),  # 왼쪽 손목
            16: (-0.5, 0.3),  # 오른쪽 손목
        }

        for idx, landmark in enumerate(result['landmarks']):
            if idx in key_joints:
                offset_x, offset_y = key_joints[idx]
                landmark['x'] += offset_x
                landmark['y'] += offset_y

# 전역변수 초기화 함수
def reset_globals():
    global accel_seq_buffer, fall_detected, is_first, distances

    # 시퀀스 버퍼 초기화
    accel_seq_buffer.clear()

    # 낙상 감지 플래그 초기화
    fall_detected = False

    # 첫 프레임 여부 초기화
    is_first = True

    # 뼈 길이 초기화
    distances = {}

    print("🌀 전역 상태가 초기화되었습니다.")
