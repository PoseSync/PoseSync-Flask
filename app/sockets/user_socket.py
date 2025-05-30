import time

import numpy as np
from flask import request
from flask_socketio import emit, disconnect

# AI 모델 가져오기
from app.ai.ai_model import fall_model
from app.controllers.user_controller import handle_data_controller
from app.services.body_service.body_spec_service import get_all_body_info
from app.services.user_info_service import get_exercise_set_with_phone_number, save_updated_exercise_set, get_next_exercise_set
# 공유 전역 상태 가져오기
from app.shared.global_state import (
    accel_seq_buffer,
    fall_detected,
    is_first,
    current_user_body_type,
    current_user_bone_lengths,
    client_sid,
    counter,
    reset_globals, initialize_exercise_counter,
    is_exist, stop_monitoring
)
# 가속도 계산
from app.util.calculate_landmark_accerlation import calculate_acceleration

# 전화 걸기
from app.util.call import call_user
from app.util.pose_landmark_enum import PoseLandmark  # id→공식명 enum
from app.util.pose_transform import process_pose_landmarks, reverse_pose_landmarks

# 새로 추가: DB에서 뼈길이 가져오는 함수
from app.services.body_service.body_analysis_service import get_user_bone_lengths

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

    # 운동 사이 쉬는 시간에도 낙상 감지
    @socketio.on('monitor_fall')
    def monitor_fall(data):
        global is_first, fall_detected, client_sid

        client_sid = request.sid
        print('모니터 뻘 호출')
        try:
            landmarks = data.get('landmarks', [])
            request_id = data.get('requestId')

            fall = False

            # 가속도 계산 및 낙상 감지 로직
            acceleration = calculate_acceleration(landmarks)
            if acceleration:
                vec = acceleration["head_acceleration"] + acceleration["pelvis_acceleration"]
                accel_seq_buffer.append(vec)

                if len(accel_seq_buffer) >= 30:
                    model_input = np.array(list(accel_seq_buffer)[-30:]).reshape(1, 30, 6)
                    prediction = fall_model.predict(model_input, verbose=0)
                    fall = bool(prediction[0][0] > 0.95)

                    print(f"낙상 감지 예측값: {prediction[0][0]}")
                    if fall and not fall_detected:
                        print("########## 🚨 낙상 감지 🚨 ##########")
                        fall_detected = True

                        # ✅ 새로운 낙상 감지 시 이전 중단 신호 초기화
                        stop_monitoring.clear()
                        print("🔄 새로운 낙상 감지로 인한 모니터링 재시작")

                        # ✅ 낙상 감지 알림을 즉시 전송 (한 번만)
                        result = {
                            'requestId': request_id,
                            'is_fall': True
                        }
                        socketio.emit('result', result, to=client_sid)
                        print(f'🚨 낙상 감지 알림 전송 => {result}')

                        wait_time = 30
                        interval = 1

                        # 30초 대기 로직 (emit 없이 대기만)
                        for i in range(wait_time):
                            # Event가 설정되었는지 확인 (non-blocking)
                            if stop_monitoring.is_set():
                                print("사람이 없어졌습니다. 호출 중단.")
                                print(f"########## 모니터링 중단됨 #############")

                                fall_detected = False           # 반드시 False 로
                                stop_monitoring.clear()  # (권장) Event 재사용 준비

                                # ✅ 취소 시에만 추가 emit (낙상 상태 해제)
                                cancel_result = {
                                    'requestId': request_id,
                                    'is_fall': False
                                }
                                socketio.emit('result', cancel_result, to=client_sid)
                                print(f'🚨 낙상 취소 알림 전송 => {cancel_result}')
                                return

                            socketio.sleep(interval)
                            print(f'{i + 1}초 대기 중...')

                        fall_detected = False

                        # 여전히 모니터링 중이면 전화 걸기
                        if not stop_monitoring.is_set():
                            print("############# 전화 걸기 ###############")
                            # call_user()
                            print('📞📞📞📞📞📞전화 걸기 완료')

                        # ✅ 낙상 처리 완료 후 return (추가 emit 방지)
                        return

            # ✅ 일반적인 경우 (낙상이 아닌 경우)의 결과 전송
            # 클라이언트의 fallDetected 상태 동기화를 위해 필요
            result = {
                'requestId': request_id,
                'is_fall': False  # 평상시에는 항상 False
            }
            socketio.emit('result', result, to=client_sid)

        except Exception as e:
            print(f"❌ 낙상 감지 데이터 처리 중 예외 발생: {e}")
            import traceback
            traceback.print_exc()
            emit('result', {'error': '낙상 감지 서버 내부 오류가 발생했습니다.'})

    @socketio.on('disconnect_monitor')
    def disconnect_monitor(data):
        global is_first,client_sid

        phone_number = data.get('phoneNumber')

        is_first = True

        if client_sid:
            disconnect(sid=client_sid)
            client_sid = None

        reset_globals()
        print(f'🧹 연결 해제됨: {phone_number}')

    @socketio.on('exercise_data')
    def handle_exercise_data(data):
        global is_first, fall_detected, current_user_body_type, current_user_bone_lengths, client_sid
        start_time = time.perf_counter()
        print('exercise_data 호출')
        # 현재 연결된 클라이언트의 SID 저장
        client_sid = request.sid

        try:
            # 클라이언트에서 받은 원본 랜드마크 데이터
            landmarks = data.get('landmarks', [])
            phone_number = data.get('phoneNumber')
            exercise_type = data.get('exerciseType')
            request_id = data.get('requestId')

            # 첫 데이터 패킷일 때만 body_type과 뼈길이 데이터 가져오기
            if is_first:
                try:
                    # 모든 body_type + body_data 한 번에 조회
                    current_user_body_type = get_all_body_info(phone_number)
                    initialize_exercise_counter(exercise_type)  # 운동 카운터 초기화

                    # ✅ DB에서 뼈길이 데이터 가져오기 (필수)
                    db_bone_lengths = get_user_bone_lengths(phone_number)
                    if not db_bone_lengths:
                        raise Exception(f"DB에 뼈길이 데이터가 없습니다. 체형 분석을 먼저 진행해주세요: {phone_number}")

                    # 🦴🦴🦴 뼈길이 전역변수에 저장
                    current_user_bone_lengths = db_bone_lengths

                    print(f"✅ 전체 체형 정보 로드 완료: {current_user_body_type.keys()}")

                    is_first = False

                except Exception as e:
                    print(f"❌ 사용자 데이터 로드 실패: {e}")
                    emit('result', {'error': f'사용자 데이터 로드 실패: {str(e)}'})
                    return

            if current_user_body_type and current_user_bone_lengths:
                data['body_type'] = current_user_body_type
                data['bone_lengths'] = current_user_bone_lengths
            else:
                raise Exception("체형 정보가 없습니다")

            fall = False

            # 1. 가속도 계산 및 시퀀스 버퍼에 누적
            acceleration = calculate_acceleration(landmarks)
            if acceleration:
                # head와 pelvis의 평균 가속도를 [x, y, z]
                vec = acceleration["head_acceleration"] + acceleration["pelvis_acceleration"]
                accel_seq_buffer.append(vec)

                # 버퍼가 30개 이상일 때 매 프레임마다 예측 수행
                if len(accel_seq_buffer) >= 30:
                    model_input = np.array(list(accel_seq_buffer)[-30:]).reshape(1, 30, 6)
                    prediction = fall_model.predict(model_input, verbose=0)
                    fall = bool(prediction[0][0] > 0.95)

                    print(f"낙상 감지 예측값: {prediction[0][0]}")
                    if fall and not fall_detected:
                        print("########## 🚨 낙상 감지 🚨 ##########")
                        fall_detected = True

                        # ✅ 새로운 낙상 감지 시 이전 중단 신호 초기화
                        stop_monitoring.clear()
                        print("🔄 새로운 낙상 감지로 인한 모니터링 재시작")

                        # ✅ 낙상 감지 알림을 즉시 전송 (한 번만)
                        fall_result = {
                            'requestId': request_id,
                            'is_fall': True
                        }
                        print(f'🚨 [EXERCISE_DATA] 낙상 감지! client_sid: {client_sid}, requestId: {request_id}')
                        socketio.emit('result', fall_result, to=client_sid)
                        print(f'🚨 [EXERCISE_DATA] 낙상 감지 알림 전송 완료 => {fall_result}')

                        # 즉시 flush하여 전송 보장
                        socketio.sleep(0.1)

                        wait_time = 30
                        interval = 1

                        # 30초 대기 로직 (emit 없이 대기만)
                        for i in range(wait_time):
                            # Event가 설정되었는지 확인 (non-blocking)
                            if stop_monitoring.is_set():
                                print("사람이 없어졌습니다. 호출 중단.")
                                print(f"########## 모니터링 중단됨 #############")

                                fall_detected = False  # 반드시 False 로
                                stop_monitoring.clear()  # (권장) Event 재사용 준비

                                # ✅ 취소 시에만 추가 emit (낙상 상태 해제)
                                cancel_result = {
                                    'requestId': request_id,
                                    'is_fall': False
                                }
                                print(f'🚨 [EXERCISE_DATA] 낙상 취소! requestId: {request_id}')
                                socketio.emit('result', cancel_result, to=client_sid)
                                print(f'🚨 [EXERCISE_DATA] 낙상 취소 알림 전송 완료 => {cancel_result}')
                                return

                            socketio.sleep(interval)
                            print(f'{i + 1}초 대기 중...')

                        fall_detected = False

                        # 여전히 모니터링 중이면 전화 걸기
                        if not stop_monitoring.is_set():
                            print("############# 전화 걸기 ###############")
                            # call_user()
                            print('📞📞📞📞📞📞전화 걸기 완료')

                        # ✅ 낙상 처리 완료 후 return (추가 emit 방지)
                        return

            # ✅ 일반적인 운동 처리 로직 (낙상이 아닌 경우)
            # 사람 중심 좌표계로 변환 및 정규화
            transformed_landmarks, transform_data = process_pose_landmarks(landmarks)

            # 변환된 랜드마크로
            data['landmarks'] = transformed_landmarks
            data['__transformData'] = transform_data

            # id → name 필드 보강
            for lm in data['landmarks']:
                lm['name'] = PoseLandmark(lm['id']).name

            # 컨트롤러에서 데이터 처리 (가이드라인 생성)
            result = handle_data_controller(data)

            # 가이드라인 랜드마크를 시각화를 위해 원본 좌표계로 역변환
            visualization_landmarks = reverse_pose_landmarks(
                result['landmarks'],
                transform_data
            )

            # 시각화용 랜드마크 추가하고 원본 제거
            result['visualizationLandmarks'] = visualization_landmarks

            # 레이턴시 측정
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            result['latency'] = round(elapsed_ms, 2)

            # 중요: requestId를 결과에 포함
            result['requestId'] = request_id

            # ✅ 낙상여부를 반환 데이터에 추가 (평상시에는 항상 False)
            result['is_fall'] = False

            # 클라이언트에서 사용하지 않는 데이터 바로 삭제
            del result['landmarks']  # 원본 변환 랜드마크 제거 (네트워크 부하 감소)
            del result['__transformData']  # 변환 데이터 삭제
            del result['body_type']  # 체형 데이터 삭제
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
        global is_first,client_sid

        print('disconnect_client: 패킷 호출됨')

        phone_number = data.get('phoneNumber')
        print(f"disconnect_client: {phone_number} 연결 해제 요청")
        # 지금까지 한 운동 횟수
        current_count = data.get('count')
        print(f"disconnect_client: 현재 운동 횟수: {current_count}")

        # 받아온 phoneNumber로 ExerciseSet 객체 GET
        exercise_set = get_exercise_set_with_phone_number(phone_number)
        print(f"disconnect_client: exercise_set: {exercise_set}")

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

            # UPDATE된 updated_exercise_set 객체, 다음 운동 몇번째 세트인지 GET
            updated_exercise_set, set_number = save_updated_exercise_set(exercise_set)
            print(f"disconnect_client: updated_exercise_set: {updated_exercise_set}")

            # 인덱스는 0부터 시작이므로 +1, 만약 다음 운동이 없다면 +1을 한 결과, set_number = 0이 됨.
            set_number = int(set_number) + 1

            # 다음 운동 세트 가져오기, 다음 운동이 없다면 None 즉, null 반환
            next_set = get_next_exercise_set(updated_exercise_set.id)

            # 다음 운동 세트가 있다면 True, 없으면 False
            is_last = True
            if next_set:
                is_last = False

            # 끝난 운동 세트의 정보 클라이언트로 전송
            if updated_exercise_set:
                # 다음 운동 데이터가 없다면 => 다음 운동 관련 데이터는 다 null로 주고, is_last는 True 전달
                if is_last:
                    print(f"✅ 다음 운동 세트가 없습니다: {phone_number}")
                    socketio.emit('next', {
                    # 다음 운동 세트 번호
                    "set_number": None,
                    # 다음 운동 무게
                    "next_weight": None,
                    # 다음 운동 횟수
                    "next_target_count": None,
                    # 다음 운동 있는지 없는지 여부
                    "is_last": is_last,
                    # 횟수 초기화 용도
                    "count": 0
                }, to=client_sid)
                # 다음 운동 데이터가 있을 경우
                else:
                    print(f"✅ 다음 운동 세트가 있습니다: {phone_number}, set_number: {set_number}, next_set: {next_set}")
                    socketio.emit('next', {
                    # 다음 운동 세트 번호
                    "set_number": set_number,
                    # 다음 운동 무게
                    "next_weight": next_set.exercise_weight,
                    # 다음 운동 횟수
                    "next_target_count": next_set.target_count,
                    # 다음 운동 있는지 없는지 여부
                    "is_last": is_last,
                    # 횟수 초기화 용도
                    "count": 0
                }, to=client_sid)
        else:
            print(f"⚠️ 사용자에 대한 운동 세트 정보가 없습니다: {phone_number}")

        # 다음 세트 시작 시 다시 각 landmark 사이의 거리를 구하기 위해서 is_first 값 변경
        is_first = True

        # 소켓 연결 끊음.
        if client_sid:
            disconnect(sid=client_sid)
            client_sid = None

        # 전역변수 초기화
        reset_globals()
        print(f'🧹 연결 해제됨: {phone_number}')