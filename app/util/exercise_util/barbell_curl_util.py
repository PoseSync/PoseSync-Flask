import math
import numpy as np
from app.util.math_util import normalize_vector, vector_angle_deg

# 상완 타입별 바벨컬 가이드라인
BARBELL_CURL_GUIDELINE_BY_ARM_TYPE = {
    "LONG": {
        "grip_width_ratio": 1.1,  # 어깨 너비의 1.1배
        "min_forearm_angle": 10.0,  # 전완-상완 최소 각도
        "torso_arm_angle": 0.0  # 몸통-상완 각도
    },
    "AVG": {
        "grip_width_ratio": 1.05,
        "min_forearm_angle": 7.5,
        "torso_arm_angle": 5.0
    },
    "SHORT": {
        "grip_width_ratio": 1.0,
        "min_forearm_angle": 5.0,
        "torso_arm_angle": 10.0
    }
}


def calculate_elbow_position_for_barbell_curl(
        shoulder_coord: list,
        hip_coord: list,
        current_elbow_coord: list,
        arm_type: str,
        upper_arm_length: float,
        side: str = "right"
) -> list:
    """
    바벨컬을 위한 팔꿈치 위치 계산
    - 팔꿈치는 몸통 옆에 고정
    - 상완 타입별로 몸통과의 각도 조정

    Args:
        shoulder_coord: 어깨 좌표 [x, y, z]
        hip_coord: 엉덩이 좌표 [x, y, z]
        current_elbow_coord: 현재 팔꿈치 좌표 [x, y, z]
        arm_type: 상완 타입 ("LONG", "AVG", "SHORT")
        upper_arm_length: 상완 길이
        side: 팔 방향 ("left" or "right")

    Returns:
        list: 계산된 팔꿈치 좌표 [x, y, z]
    """
    guideline = BARBELL_CURL_GUIDELINE_BY_ARM_TYPE.get(arm_type, BARBELL_CURL_GUIDELINE_BY_ARM_TYPE["AVG"])
    torso_arm_angle = guideline["torso_arm_angle"]

    shoulder_x, shoulder_y, shoulder_z = shoulder_coord
    hip_x, hip_y, hip_z = hip_coord
    current_elbow_y = current_elbow_coord[1]  # 현재 팔꿈치 Y값 유지

    # 몸통 방향 벡터 (엉덩이 → 어깨)
    torso_vector = np.array([
        shoulder_x - hip_x,
        shoulder_y - hip_y,
        shoulder_z - hip_z
    ])
    torso_vector = normalize_vector(torso_vector)

    # 상완이 몸통과 이루는 각도 적용
    angle_rad = math.radians(torso_arm_angle)

    # 기본적으로 팔꿈치는 어깨 바로 아래 (X 좌표 동일)
    elbow_x = shoulder_x

    # Z 좌표는 각도에 따라 앞쪽으로 조정
    # 몸통 기준으로 앞쪽으로 나가는 정도
    z_offset = math.sin(angle_rad) * upper_arm_length * 0.3  # 0.3은 조정 계수
    elbow_z = shoulder_z + z_offset

    # Y 좌표는 현재 값 유지 (수직 이동만 허용)
    elbow_y = current_elbow_y

    # 팔꿈치가 어깨보다 너무 높이 올라가지 않도록 제한
    max_elbow_y = shoulder_y - upper_arm_length * 0.5
    if elbow_y < max_elbow_y:
        elbow_y = max_elbow_y

    print(f"[{side}] Elbow position: torso_angle={torso_arm_angle}°, z_offset={z_offset:.3f}")

    return [elbow_x, elbow_y, elbow_z]


def calculate_wrist_position_for_barbell_curl(
        elbow_coord: list,
        current_wrist_coord: list,
        shoulder_width: float,
        forearm_length: float,
        arm_type: str,
        side: str = "right"
) -> list:
    """
    바벨컬을 위한 손목 위치 계산
    - 팔꿈치를 중심으로 회전
    - 상완 타입별 그립 너비와 최소 각도 적용

    Args:
        elbow_coord: 팔꿈치 좌표 [x, y, z]
        current_wrist_coord: 현재 손목 좌표 [x, y, z]
        shoulder_width: 어깨 너비
        forearm_length: 전완 길이
        arm_type: 상완 타입
        side: 팔 방향

    Returns:
        list: 계산된 손목 좌표 [x, y, z]
    """
    guideline = BARBELL_CURL_GUIDELINE_BY_ARM_TYPE.get(arm_type, BARBELL_CURL_GUIDELINE_BY_ARM_TYPE["AVG"])
    grip_width_ratio = guideline["grip_width_ratio"]
    min_forearm_angle = guideline["min_forearm_angle"]

    elbow_x, elbow_y, elbow_z = elbow_coord
    current_wrist_x, current_wrist_y, current_wrist_z = current_wrist_coord

    # 현재 전완 벡터 (팔꿈치 → 손목)
    forearm_vector = np.array([
        current_wrist_x - elbow_x,
        current_wrist_y - elbow_y,
        current_wrist_z - elbow_z
    ])

    # 수직 벡터 (아래 방향)
    vertical_vector = np.array([0, 1, 0])

    # 현재 전완 각도 계산
    current_angle = vector_angle_deg(forearm_vector, vertical_vector)

    # 최소 각도 체크 및 보정
    if current_angle < min_forearm_angle:
        print(f"[{side}] Adjusting forearm angle: {current_angle:.1f}° → {min_forearm_angle}°")
        angle_rad = math.radians(min_forearm_angle)
    else:
        angle_rad = math.radians(current_angle)

    # 손목 Y 좌표: 팔꿈치에서 전완 길이만큼 아래
    wrist_y = elbow_y + forearm_length * math.cos(angle_rad)

    # 손목 Z 좌표: 각도에 따라 앞쪽으로
    wrist_z = elbow_z + forearm_length * math.sin(angle_rad)

    # 손목 X 좌표: 그립 너비에 따라 결정
    grip_width = shoulder_width * grip_width_ratio
    half_grip_width = grip_width / 2

    if side == "right":
        wrist_x = half_grip_width
    else:  # left
        wrist_x = -half_grip_width

    print(f"[{side}] Wrist position: grip_width={grip_width:.3f}, angle={math.degrees(angle_rad):.1f}°")

    return [wrist_x, wrist_y, wrist_z]


def create_symmetric_arm_positions(
        right_elbow_pos: list,
        right_wrist_pos: list,
        body_center_x: float = 0.0
) -> tuple:
    """
    오른팔 위치를 기준으로 왼팔 대칭 위치 생성

    Args:
        right_elbow_pos: 오른팔 팔꿈치 위치
        right_wrist_pos: 오른팔 손목 위치
        body_center_x: 몸 중심선 X 좌표

    Returns:
        tuple: (left_elbow_pos, left_wrist_pos)
    """
    # 왼팔 팔꿈치: X 좌표만 대칭
    left_elbow_pos = [
        body_center_x - (right_elbow_pos[0] - body_center_x),  # X 대칭
        right_elbow_pos[1],  # Y 동일
        right_elbow_pos[2]  # Z 동일
    ]

    # 왼팔 손목: X 좌표만 대칭
    left_wrist_pos = [
        body_center_x - (right_wrist_pos[0] - body_center_x),  # X 대칭
        right_wrist_pos[1],  # Y 동일
        right_wrist_pos[2]  # Z 동일
    ]

    return left_elbow_pos, left_wrist_pos