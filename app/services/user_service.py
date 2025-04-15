import numpy as np
from app.util.squat_util import get_theta, get_femur, height_hip_knee, get_pi
from app.util.pose_landmark_enum import PoseLandmark
from app.util.math_util import normalize_vector
from app.util.body_type_util import get_user_arm_type
import math

def process_squat(data):
    landmarks = data.get("landmarks", [])

    # 양쪽 고관절 중심 좌표 계산
    left_hip = landmarks[PoseLandmark.LEFT_HIP]
    right_hip = landmarks[PoseLandmark.RIGHT_HIP]

    # 왼쪽 무릎, 왼쪽 고관절, 오른쪽 무릎, 오른쪽 고관절 landmark를 매개변수로 넘겨준 후 theta 얻기
    left_knee = landmarks[PoseLandmark.LEFT_KNEE]
    right_knee = landmarks[PoseLandmark.RIGHT_KNEE]
    theta = get_theta(left_hip, right_hip, left_knee, right_knee)

    # 대퇴골 길이, 양쪽 대퇴골 길이는 같다라는 가정 하에 왼쪽 무릎과 고관절만 매개변수로 넘겨줌
    # femur = get_femur(left_hip, left_knee)
    # 대퇴골 길이는 추후에 DB 연동해서 가져올 예정
    femur = 43

    # 고관절과 무릎 사이의 거리, 양쪽 고관절 높이가 같다라는 가정 하에 왼쪽 고관절과 왼쪽 무릎만 매개변수로 넘겨줌
    delta_y = height_hip_knee(left_hip, left_knee)

    # r 구하기
    r = math.sqrt((femur ** 2) - (delta_y ** 2))

    # pi 구하기
    pi = get_pi(left_hip, right_hip)

    # 라디안으로 변환
    pi_rad = math.radians(pi)
    theta_rad = math.radians(theta)

    # 각 무릎의 x, z 좌표 계산 (라디안 값으로 삼각함수 계산)
    left_knee_x = left_hip.get('x') + r * np.cos(pi_rad - (theta_rad / 2))
    left_knee_z = left_hip.get('z') + r * np.sin(pi_rad - (theta_rad / 2))

    right_knee_x = right_hip.get('x') + r * np.cos(pi_rad + (theta_rad / 2))
    right_knee_z = right_hip.get('z') + r * np.sin(pi_rad + (theta_rad / 2))

    # 무릎 위치 업데이트 (item == data의 실제값과 동일 : item을 초기화하면 data도 수정됨)
    landmarks[PoseLandmark.LEFT_KNEE]['x'] = left_knee_x
    landmarks[PoseLandmark.LEFT_KNEE]['z'] = left_knee_z
    landmarks[PoseLandmark.RIGHT_KNEE]['x'] = right_knee_x
    landmarks[PoseLandmark.RIGHT_KNEE]['z'] = right_knee_z

    return data


def process_dumbel_sholderPress(data):

    landmarks = data.get("landmarks", [])
    phone_number = data.get("phoneNumber") # 개인식별자

    arm_type = get_user_arm_type(phone_number) # 사용자의 상완 체형타입 저장

    #양쪽 어깨(11, 12)좌표 가져오기
    left_shoulder = landmarks[PoseLandmark.LEFT_SHOULDER]
    right_shoulder = landmarks[PoseLandmark.RIGHT_SHOULDER]
    #팔꿈치 (13, 14)
    left_elbow = landmarks[PoseLandmark.LEFT_ELBOW]
    right_elbow = landmarks[PoseLandmark.RIGHT_ELBOW]
    #손목 (15, 16)
    left_wrist = landmarks[PoseLandmark.LEFT_WRIST]
    right_wrist = landmarks[PoseLandmark.RIGHT_WRIST]

    # 정규화 상완 벡터: 어깨 → 팔꿈치
    left_upper_arm_vec = normalize_vector(np.array([
        left_elbow['x'] - left_shoulder['x'],
        left_elbow['y'] - left_shoulder['y'],
        left_elbow['z'] - left_shoulder['z']
    ]))
    right_upper_arm_vec = normalize_vector(np.array([
        right_elbow['x'] - right_shoulder['x'],
        right_elbow['y'] - right_shoulder['y'],
        right_elbow['z'] - right_shoulder['z']
    ]))

    # 정규화 전완 벡터: 팔꿈치 → 손목
    left_forearm_vec = normalize_vector(np.array([
        left_wrist['x'] - left_elbow['x'],
        left_wrist['y'] - left_elbow['y'],
        left_wrist['z'] - left_elbow['z']
    ]))
    right_forearm_vec = normalize_vector(np.array([
        right_wrist['x'] - right_elbow['x'],
        right_wrist['y'] - right_elbow['y'],
        right_wrist['z'] - right_elbow['z']
    ]))

    # 정규화 어깨 라인 벡터: 왼쪽 → 오른쪽 어깨
    shoulder_line_vec = normalize_vector(np.array([
        right_shoulder['x'] - left_shoulder['x'],
        right_shoulder['y'] - left_shoulder['y'],
        right_shoulder['z'] - left_shoulder['z']
    ]))
    
    

    return data #수정된 data