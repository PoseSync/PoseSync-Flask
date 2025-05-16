import math

from flask_socketio import emit, SocketIO, disconnect
from flask import request
from app.controllers.user_controller import handle_data_controller
from app.services.user_info_service import get_exercise_set, save_updated_exercise_set
from app.util.calculate_landmark_distance import connections, calculate_named_linked_distances, \
    map_distances_to_named_keys, bone_name_map
from app.util.landmark_stabilizer import landmark_stabilizer
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

# socketio = SocketIO(cors_allowed_origins="*")


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

#-----------------------------------------------------------------------------------------------------------

def register_user_socket(socketio):

    # 소켓 연결
    @socketio.on('connection')
    def handle_connect(data):
        phone_number = data.get('phoneNumber')

        clients[phone_number] = request.sid
        global is_first
        is_first = True  # 첫 서버연결 때 운동 패킷 첫 연결여부 True
        print(f' 클라이언트 연결됨 : {phone_number} -> SID {request.sid}')


    # 운동 세트 시작할 때
    # @socketio.on('restart')
    # def handle_reconnect(data):
    #     phone_number = data.get('phoneNumber')
    #     clients[phone_number] = request.sid

    #     # 운동 세트 시작할 때 운동 횟수, 이름 보내줌.
    #     socketio.emit('start', {
    #         "exercise_name": record_list[0].exercise_name,
    #         "exercise_weight": record_list[0].exercise_weight
    #     },
    #     to=request.sid
    #     )
    #     print(f' 클라이언트 연결됨 : {phone_number} -> SID {request.sid}')


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


# -----------------------------------------------------------------------------------------------------------

    # 클라이언트 수동 연결 해제 요청 처리, 1세트 운동 끝나고 ExerciseSet is_finished, is_success 업데이트 후 DB에 저장
    # DB에 저장된 ExerciseSet 객체를 마지막으로 소켓을 통해 클라이언트로 반환 후 소켓 disconnection
    @socketio.on('disconnect_client')
    def handle_disconnect_client(data):
        global is_first, distances   # 뼈 길이 배열
        phone_number = data.get('phoneNumber')

        # 지금까지 한 운동 횟수
        current_count = data.get('count')
        removed = clients.pop(phone_number, None)
        
        # 받아온 phoneNumber로 ExerciseSet 객체 GET
        exercise_set = get_exercise_set(phone_number)

        # exercise_cnt 업데이트
        # 지금까지 한 운동 횟수 업데이트
        exercise_set.current_count = current_count
        # 운동 종료 업데이트
        exercise_set.is_finished = True
        # 목표 운동 횟수 채우지 않았다면 실패한 운동 세트
        if exercise_set.current_count < exercise_set.target_count:
            exercise_set.is_success = False
        # 목표 운동 횟수를 채웠다면 성공한 운동 세트
        else:
            exercise_set.is_success = True

        # UPDATE된 updated_exercise_set 객체 GET
        updated_exercise_set = save_updated_exercise_set(exercise_set)

        # 끝난 운동 세트의 정보 클라이언트로 전송
        if updated_exercise_set:
            socketio.emit('next', {
                "exerciseType": updated_exercise_set.exercise_type,
                "current_count": updated_exercise_set.current_count,
                "exercise_weight": updated_exercise_set.exercise_weight
            }, to=removed)
        if removed:
            # 다음 세트 시작 시 다시 각 landmark 사이의 거리를 구하기 위해서 is_first 값 변경
            is_first = True
            reset_globals()
            print(f'🧹 연결 해제됨: {phone_number}')



    @socketio.on('exercise_data')
    def handle_exercise_data(data):
        global is_first, distances, fall_detected
        start_time = time.perf_counter()
        try:
            # 클라이언트에서 받은 원본 랜드마크 데이터
            landmarks = data.get('landmarks', [])

            # # 1. 랜드마크 안정화 적용 (프레임 내 떨림 감소)
            # try:
            #     landmarks = landmark_stabilizer.stabilize_landmarks(landmarks, dead_zone=0.05)
            #     data['landmarks'] = landmarks  # 안정화된 랜드마크로 업데이트
            # except Exception as e:
            #     print(f"랜드마크 안정화 중 오류 발생: {e}")
            #     # 오류 발생 시 원본 landmarks 사용

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



            # --------------------------------------------------------------------------------------

            # 사람 중심 좌표계로 변환 및 정규화
            transformed_landmarks, transform_data = process_pose_landmarks(landmarks)

            # 변환된 랜드마크로
            data['landmarks'] = transformed_landmarks
            data['__transformData'] = transform_data

           # id → name 필드 보강
            for lm in data['landmarks']:
                lm['name'] = PoseLandmark(lm['id']).name

            # 2. 첫프레임 or 뼈 길이 없는경우 ->  뼈 길이 계산 및 이동 평균 적용 (프레임 간 변동 감소)
            # 사용자 기준으로 변환된 좌표를 사용해서 구함 (가이드라인 생성 로직에서 사용하는 좌표계)
            if not distances:
                current_distances = calculate_named_linked_distances(data['landmarks'], connections)
                current_distances = map_distances_to_named_keys(current_distances, bone_name_map)
                distances = current_distances
                print('🦴🦴🦴🦴🦴뼈 길이 측정 완료')
                print(f"뼈 길이 : {distances}")

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


# 전역변수 초기화 함수
def reset_globals():
    global accel_seq_buffer, fall_detected, is_first, distances, current_distances

    # 시퀀스 버퍼 초기화
    accel_seq_buffer.clear()

    # 낙상 감지 플래그 초기화
    fall_detected = False

    # 첫 프레임 여부 초기화
    is_first = True

    # 뼈 길이 초기화
    distances = {}
    print('❌❌❌뼈 길이 데이터 빈 배열로 초기화 완료❌❌❌')


    print("🌀 전역 상태가 초기화되었습니다.")
