import numpy as np
from app.util.pose_landmark_enum import PoseLandmark
import copy
from collections import deque
import time

# AI 모델 가져오기
from app.ai.ai_model import fall_model

# 가속도 계산
from app.util.calculate_landmark_accerlation import calculate_acceleration

start_hip_y = None  # 스쿼트 시작 시 고관절 높이 저장
is_descending = True  # 현재 내려가는 상태인지 여부 (True면 내려가는 중)
hip_to_knee_length = None  # 고관절-무릎 길이 저장
knee_to_ankle_length = None  # 무릎-발목 길이 저장
squat_count = 0  # 스쿼트 횟수

# 시퀀스 버퍼 (60프레임)
accel_seq_buffer = deque(maxlen=30)

fall_detected = False

def process_squat(data):
    # 클라이언트로부터 landmarks 데이터를 받음.
    # -> 내려가는 중이면 squat_down, 내려갔다가 다시 올라가는 동작이면 squat_up 함수 호출
    # -> 최저점 도달하면 올라가기 전환, 올라가서 원위치 도달하면 스쿼트 횟수 증가

    global start_hip_y, is_descending, hip_to_knee_length, knee_to_ankle_length, squat_count
    global fall_detected

    landmarks = data.get("landmarks", [])

    if not landmarks:
        raise ValueError("landmarks 데이터가 없습니다")
    
    # 원본을 절대 수정하지 않게 깊은 복사(deep copy) 사용
    landmarks = copy.deepcopy(landmarks) 

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
            fall = bool(prediction[0][0] > 0.5)
            print(f"예측값: {prediction[0][0]}")
            if fall and not fall_detected:
                print("##########  낙상 감지 ##########")
                fall_detected = True
            elif not fall:
                fall_detected = False  # 감지가 끝나면 다시 초기화

    if start_hip_y is None:
        start_hip_y = landmarks[PoseLandmark.LEFT_HIP]['y']
        hip_to_knee_length, knee_to_ankle_length = calculate_joint_lengths(landmarks)

    left_hip = landmarks[PoseLandmark.LEFT_HIP]

    if is_descending:
        landmarks = squat_down_with_kinematics(landmarks, hip_to_knee_length, knee_to_ankle_length)
        if should_start_standup(start_hip_y, left_hip['y']):
            is_descending = False
    else:
        landmarks = squat_up_with_kinematics(landmarks, hip_to_knee_length, knee_to_ankle_length)
        if left_hip['y'] <= start_hip_y + 0.02:  # 거의 원래 높이에 복귀했으면
            squat_count += 1  # 스쿼트 횟수 추가
            is_descending = True  # 다시 내려가기 시작
    data["landmarks"] = landmarks
    # 반환하는 data에 횟수 추가
    data["count"] = squat_count

    return data


def calculate_joint_lengths(landmarks):
    """
    hip→knee, knee→ankle 관절 길이를 계산해서 반환
    (왼쪽 기준으로 계산)
    """
    def distance(a, b):
        return np.linalg.norm(np.array([a['x'], a['y'], a['z']]) - np.array([b['x'], b['y'], b['z']]))

    left_hip = landmarks[PoseLandmark.LEFT_HIP]
    left_knee = landmarks[PoseLandmark.LEFT_KNEE]
    left_ankle = landmarks[PoseLandmark.LEFT_ANKLE]

    hip_to_knee = distance(left_hip, left_knee)
    knee_to_ankle = distance(left_knee, left_ankle)

    return hip_to_knee, knee_to_ankle

# 내려가는 동작
def squat_down_with_kinematics(landmarks, hip_to_knee_length, knee_to_ankle_length):
    """
    관절 길이를 유지하면서 고관절을 내려주고,
    무릎을 앞으로 이동시켜 스쿼트 다운(내려가기) 동작을 만든다.
    """

    left_hip = landmarks[PoseLandmark.LEFT_HIP]
    left_knee = landmarks[PoseLandmark.LEFT_KNEE]
    left_ankle = landmarks[PoseLandmark.LEFT_ANKLE]

    right_hip = landmarks[PoseLandmark.RIGHT_HIP]
    right_knee = landmarks[PoseLandmark.RIGHT_KNEE]
    right_ankle = landmarks[PoseLandmark.RIGHT_ANKLE]

    # 1. 고관절 y축 이동 (내려가기)
    hip_drop_speed = 0.01
    left_hip['y'] += hip_drop_speed
    right_hip['y'] += hip_drop_speed

    # 2. 무릎 y, z 조정 (hip 기준으로 내려가면서 앞으로 이동)
    left_knee['y'] = left_hip['y'] + hip_to_knee_length * np.cos(np.radians(45))
    left_knee['z'] = left_hip['z'] - hip_to_knee_length * np.sin(np.radians(45))

    right_knee['y'] = right_hip['y'] + hip_to_knee_length * np.cos(np.radians(45))
    right_knee['z'] = right_hip['z'] - hip_to_knee_length * np.sin(np.radians(45))

    return landmarks

# 올라가는 동작
def squat_up_with_kinematics(landmarks, hip_to_knee_length, knee_to_ankle_length):
    """
    관절 길이를 유지하면서 고관절을 올려주고,
    무릎을 관절 각도 45도 유지하면서 따라오게 한다.
    (완전히 올라올 때만 무릎을 hip 바로 아래로 복원)
    """

    left_hip = landmarks[PoseLandmark.LEFT_HIP]
    left_knee = landmarks[PoseLandmark.LEFT_KNEE]

    right_hip = landmarks[PoseLandmark.RIGHT_HIP]
    right_knee = landmarks[PoseLandmark.RIGHT_KNEE]

    # 1. 고관절 y축 이동 (조금씩 올라가기)
    hip_rise_speed = 0.01
    left_hip['y'] -= hip_rise_speed
    right_hip['y'] -= hip_rise_speed

    # 2. 무릎 이동 (올라오는 중에는 여전히 관절 각도 유지)
    left_knee['y'] = left_hip['y'] - hip_to_knee_length * np.cos(np.radians(45))
    left_knee['z'] = left_hip['z'] + hip_to_knee_length * np.sin(np.radians(45))

    right_knee['y'] = right_hip['y'] - hip_to_knee_length * np.cos(np.radians(45))
    right_knee['z'] = right_hip['z'] + hip_to_knee_length * np.sin(np.radians(45))

    return landmarks


def should_start_standup(start_hip_y, current_hip_y, threshold=0.25):
    """
    내려간 정도가 threshold 이상이면
    내려가기 종료하고 올라가야 한다고 판단
    """
    return (current_hip_y - start_hip_y) >= threshold
