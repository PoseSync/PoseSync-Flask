# app/shared/global_state.py

from collections import deque
from app.util.pose_landmark_enum import PoseLandmark
from app.util.rep_counter import RepCounter

# 시퀀스 버퍼 (30프레임)
accel_seq_buffer = deque(maxlen=30)

# 상태 관리 전역 변수
fall_detected = False
is_first = True  # 현재 클라이언트로 전달받은 데이터가 맨 처음 데이터인지 확인
current_user_body_type = None
current_user_bone_lengths = None  # ✅ 새로 추가
client_sid = None  # 현재 연결된 클라이언트의 세션 ID
counter = None # 운동 카운터 인스턴스 - 전역으로 관리


def initialize_exercise_counter(exercise_type: str):
    """
    운동 타입에 맞춰 단일 counter 를 생성
    """
    global counter
    counter = None  # 먼저 비움

    if exercise_type == "dumbbell_shoulder_press":
        print(f'{exercise_type} 카운터 생성')
        counter = RepCounter(
            anchor_id=PoseLandmark.LEFT_EYE_INNER,  # 눈보다 위면 up 아래면 down
            moving_id=PoseLandmark.LEFT_WRIST,
            axis='y',  # y축 기준으로 판단
            down_offset=0.02,  # 어깨보다 아래로 이만큼 있으면 "down" 상태
            up_offset=0.05,  # 어깨보다 위로 이만큼 있으면 "up" 상태
            buffer_size=3,
            initial_state="down"
        )

    elif exercise_type == "barbell_curl":
        counter = RepCounter(
            anchor_id   = PoseLandmark.RIGHT_ELBOW,
            moving_id   = PoseLandmark.RIGHT_WRIST,
            axis        = 'y',
            down_offset = 0.2,
            up_offset   = 0.15,
            initial_state="down"
        )


# 전역변수 초기화 함수
def reset_globals():
    """
    소켓 연결 해제 시 전역 상태를 모두 초기화.
    카운터 자체는 reset()만 수행하고 새로 생성은 하지 않는다.
    """
    global accel_seq_buffer, fall_detected, is_first
    global current_user_body_type, current_user_bone_lengths
    global client_sid, counter

    # 기본 플래그‧버퍼 초기화
    accel_seq_buffer.clear()
    fall_detected = False
    is_first      = True
    current_user_body_type    = None
    current_user_bone_lengths = None
    client_sid = None

    # 카운터 값만 리셋
    if counter:
        counter.reset()

    print("🌀 전역 상태가 초기화되었습니다.")