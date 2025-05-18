# app/shared/global_state.py

from collections import deque
from app.util.pose_landmark_enum import PoseLandmark
from app.util.rep_counter import RepCounter

# 시퀀스 버퍼 (30프레임)
accel_seq_buffer = deque(maxlen=30)

# 상태 관리 전역 변수
fall_detected = False
is_first = True  # 현재 클라이언트로 전달받은 데이터가 맨 처음 데이터인지 확인
distances = {}  # 유저의 각 landmark 사이의 거리
current_user_body_type = None  # 추가: 전체 체형 정보를 저장할 변수
client_sid = None  # 현재 연결된 클라이언트의 세션 ID

# 운동 카운터 인스턴스 - 전역으로 관리
press_counter = None


def init_counters():
    """운동 카운터 인스턴스 초기화"""
    global press_counter

    press_counter = RepCounter(
        anchor_id=PoseLandmark.LEFT_EYE_INNER,  # 눈보다 위면 up 아래면 down
        moving_id=PoseLandmark.LEFT_WRIST,
        axis='y',  # y축 기준으로 판단
        down_offset=0.02,  # 어깨보다 아래로 이만큼 있으면 "down" 상태
        up_offset=0.1,  # 어깨보다 위로 이만큼 있으면 "up" 상태
        buffer_size=3,
        initial_state="down"
    )


# 전역변수 초기화 함수
def reset_globals():
    global accel_seq_buffer, fall_detected, is_first, distances, current_user_body_type, client_sid, press_counter

    # 시퀀스 버퍼 초기화
    accel_seq_buffer.clear()

    # 낙상 감지 플래그 초기화
    fall_detected = False

    # 첫 프레임 여부 초기화
    is_first = True

    # 뼈 길이 초기화
    distances = {}

    # 추가: 전체 체형 정보 초기화
    current_user_body_type = None

    print(f'현재 개수 : {press_counter.count}')

    # 클라이언트 SID 초기화
    client_sid = None

    press_counter.reset()

    # 항상 카운터 재초기화
    init_counters()

    print(f'{press_counter.count}')

    print('❌❌❌뼈 길이 데이터 빈 배열로 초기화 완료❌❌❌')
    print("🌀 전역 상태가 초기화되었습니다.")


# 서버 시작 시 카운터 초기화 실행
init_counters()