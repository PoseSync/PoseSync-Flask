from collections import deque

# 시퀀스 버퍼 (30프레임)
accel_seq_buffer = deque(maxlen=30)

# 상태 관리 전역 변수
fall_detected = False
is_first = True  # 현재 클라이언트로 전달받은 데이터가 맨 처음 데이터인지 확인
distances = {}  # 유저의 각 landmark 사이의 거리
current_user_body_type = None  # 현재 사용자의 체형 타입
client_sid = None  # 현재 연결된 클라이언트의 세션 ID

# 전역변수 초기화 함수
def reset_globals():
    global accel_seq_buffer, fall_detected, is_first, distances, current_user_body_type, client_sid
    
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
    
    # 클라이언트 SID 초기화
    client_sid = None
    
    print('❌❌❌뼈 길이 데이터 빈 배열로 초기화 완료❌❌❌')
    print("�� 전역 상태가 초기화되었습니다.") 