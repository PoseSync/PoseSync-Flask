import math

from flask_socketio import emit, SocketIO, disconnect
from flask import request
from app.controllers.user_controller import handle_data_controller
from app.services.user_info_service import get_exercise_set, save_updated_exercise_set
from app.util.calculate_landmark_distance import connections, calculate_named_linked_distances, \
    map_distances_to_named_keys, bone_name_map
from app.util.landmark_stabilizer import landmark_stabilizer
from app.util.pose_landmark_enum import PoseLandmark  # id→공식명 enum
import time
from app.util.pose_transform import process_pose_landmarks, reverse_pose_landmarks
from app.services.body_service.body_spec_service import get_body_info_for_dumbbell_shoulder_press

from collections import deque
import time
import numpy as np

# AI 모델 가져오기
from app.ai.ai_model import fall_model

# 가속도 계산
from app.util.calculate_landmark_accerlation import calculate_acceleration

# 전화 걸기
from app.util.call import call_user

# 공유 전역 상태 가져오기
from app.shared.global_state import (
    accel_seq_buffer, 
    fall_detected, 
    is_first, 
    distances, 
    current_user_body_type, 
    client_sid,
    reset_globals
)

# 테스트 모드 전역 변수
TEST_OFFSET_ENABLED = False  # 테스트 모드 활성화

LANDMARK_NAMES = [
    "코", "왼눈안", "왼눈", "왼눈밖", "오른눈안", "오른눈", "오른눈밖", "왼귀", "오른귀",
    "입술왼쪽", "입술오른쪽", "왼어깨", "오른어깨", "왼팔꿈치", "오른팔꿈치", "왼손목", "오른손목",
    "왼엄지", "오른엄지", "왼검지", "오른검지", "왼새끼", "오른새끼",
    "왼엉덩이", "오른엉덩이", "왼무릎", "오른무릎", "왼발목", "오른발목",
    "왼뒤꿈치", "오른뒤꿈치", "왼발끝", "오른발끝"
]


def register_user_socket(socketio):
    @socketio.on('exercise_data')
    def handle_exercise_data(data):
        global is_first, distances, fall_detected, current_user_body_type, client_sid
        start_time = time.perf_counter()

        # 현재 연결된 클라이언트의 SID 저장
        client_sid = request.sid

        try:
            # 클라이언트에서 받은 원본 랜드마크 데이터
            landmarks = data.get('landmarks', [])
            phone_number = data.get('phoneNumber')

            # 첫 데이터 패킷일 때만 body_type 가져오기
            if is_first:
                try:
                    user_body_info = get_body_info_for_dumbbell_shoulder_press(phone_number)
                    global current_user_body_type  # global 선언 확실히 해주기
                    current_user_body_type = user_body_info["arm_type"]
                    print(f'👤 첫 데이터 패킷: 사용자 body_type 설정 완료, arm_type: {current_user_body_type}')
                except Exception as e:
                    current_user_body_type = "AVG"  # 기본값 설정
                    print(f"❌ body_type 가져오기 실패: {e}, 기본값 'AVG' 사용")

            fall = False

            print(f'클라이언트에서 받자마자 => {landmarks}')

            # 1. 가속도 계산 및 시퀀스 버퍼에 누적
            acceleration = calculate_acceleration(landmarks)
            if acceleration:
                # head와 pelvis의 평균 가속도를 [x, y, z]
                vec = acceleration["head_acceleration"] + acceleration["pelvis_acceleration"]
                accel_seq_buffer.append(vec)

                print(f"[{time.time()}] ✅ accel 추가됨, 현재 길이: {len(accel_seq_buffer)}")

                # 버퍼가 30개 이상일 때 매 프레임마다 예측 수행
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

            # 사람 중심 좌표계로 변환 및 정규화
            transformed_landmarks, transform_data = process_pose_landmarks(landmarks)

            # 변환된 랜드마크로
            data['landmarks'] = transformed_landmarks
            data['__transformData'] = transform_data

            # id → name 필드 보강
            for lm in data['landmarks']:
                lm['name'] = PoseLandmark(lm['id']).name

            # 첫프레임 or 뼈 길이 없는경우 ->  뼈 길이 계산 및 이동 평균 적용 (프레임 간 변동 감소)
            if not distances:
                current_distances = calculate_named_linked_distances(data['landmarks'], connections)
                current_distances = map_distances_to_named_keys(current_distances, bone_name_map)
                distances = current_distances
                print('🦴🦴🦴🦴🦴뼈 길이 측정 완료')
                print(f"뼈 길이 : {distances}")
                is_first = False  # 첫 프레임 처리 완료

            # 서버 내부에서 사용할 수 있도록 뼈 길이 데이터 추가
            data["bone_lengths"] = distances

            # requestId 추출
            request_id = data.get('requestId')

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
            print(f'클라이언트에게 전송 => {result}')
            socketio.emit('result', result, to=client_sid)

        except Exception as e:
            print(f"❌ 데이터 처리 중 예외 발생: {e}")
            import traceback
            traceback.print_exc()
            emit('result', {'error': '서버 내부 오류가 발생했습니다.'})

    # 클라이언트 수동 연결 해제 요청 처리
    @socketio.on('disconnect_client')
    def handle_disconnect_client(data):
        global is_first, distances, current_user_body_type, client_sid
        phone_number = data.get('phoneNumber')
        # 지금까지 한 운동 횟수
        current_count = data.get('count')

        # 받아온 phoneNumber로 ExerciseSet 객체 GET
        exercise_set = get_exercise_set(phone_number)

        # exercise_set이 None이 아닌 경우에만 업데이트 수행
        if exercise_set:
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
                }, to=client_sid)
        else:
            print(f"⚠️ 사용자에 대한 운동 세트 정보가 없습니다: {phone_number}")

        # 다음 세트 시작 시 다시 각 landmark 사이의 거리를 구하기 위해서 is_first 값 변경
        is_first = True
        distances = {}
        current_user_body_type = None

        # 소켓 연결 끊음.
        if client_sid:
            disconnect(sid=client_sid)
            client_sid = None

        # 전역변수 초기화
        reset_globals()
        print(f'🧹 연결 해제됨: {phone_number}')


# 전역변수 초기화 함수
def reset_globals():
    global accel_seq_buffer, fall_detected, is_first, distances, current_user_body_type

    # 시퀀스 버퍼 초기화
    accel_seq_buffer.clear()

    # 낙상 감지 플래그 초기화
    fall_detected = False

    # 첫 프레임 여부 초기화
    is_first = True

    # 뼈 길이 초기화
    distances = {}

    # 사용자 body_type 초기화
    current_user_body_type = None

    print('❌❌❌뼈 길이 데이터 빈 배열로 초기화 완료❌❌❌')
    print("🌀 전역 상태가 초기화되었습니다.")