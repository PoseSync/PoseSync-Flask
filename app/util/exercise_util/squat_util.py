import math
import numpy as np

# 대퇴골 타입별 가이드라인
SQUAT_GUIDELINE_BY_FEMUR_TYPE = {
    "LONG": {
        "foot_width_ratio": 1.10,  # 어깨 너비의 1.10배
        "knee_angle": 55.0  # 무릎 각도 55도
    },
    "AVG": {
        "foot_width_ratio": 1.05,  # 어깨 너비의 1.05배
        "knee_angle": 45.0  # 무릎 각도 45도
    },
    "SHORT": {
        "foot_width_ratio": 1.00,  # 어깨 너비의 1.00배
        "knee_angle": 35.0  # 무릎 각도 35도
    }
}


def degrees_to_radians(deg):
    """도를 라디안으로 변환"""
    return deg * math.pi / 180


def adjust_foot_width_only(hip_center, shoulder_width, femur_type, current_left_ankle, current_right_ankle):
    """
    발 너비만 조절하고 나란하게 정렬
    - X: 고관절 중심 기준으로 대칭 배치 (너비만 조절)
    - Y: 사용자 발목의 실제 Y값 유지
    - Z: 두 발의 평균 Z값으로 나란하게 정렬

    Args:
        hip_center: [x, y, z] 엉덩이 중심 좌표
        shoulder_width: 어깨 너비
        femur_type: 대퇴골 타입 ("LONG", "AVG", "SHORT")
        current_left_ankle: 현재 왼쪽 발목 좌표
        current_right_ankle: 현재 오른쪽 발목 좌표

    Returns:
        tuple: (left_ankle_pos, right_ankle_pos)
    """
    guideline = SQUAT_GUIDELINE_BY_FEMUR_TYPE.get(femur_type, SQUAT_GUIDELINE_BY_FEMUR_TYPE["AVG"])
    foot_width = shoulder_width * guideline["foot_width_ratio"]

    # 발 너비의 절반
    half_foot_width = foot_width / 2

    # 두 발의 평균 Z값 계산 (나란하게 정렬)
    avg_z = (current_left_ankle['z'] + current_right_ankle['z']) / 2

    # 왼쪽 발목 위치 (X만 조절, Y는 그대로, Z는 평균값)
    left_ankle_pos = [
        hip_center[0] - half_foot_width,  # X: 고관절 중심 - 발너비/2
        current_left_ankle['y'],  # Y: 사용자의 실제 Y값 유지
        avg_z  # Z: 평균값으로 나란하게 정렬
    ]

    # 오른쪽 발목 위치 (X만 조절, Y는 그대로, Z는 평균값)
    right_ankle_pos = [
        hip_center[0] + half_foot_width,  # X: 고관절 중심 + 발너비/2
        current_right_ankle['y'],  # Y: 사용자의 실제 Y값 유지
        avg_z  # Z: 평균값으로 나란하게 정렬
    ]

    return left_ankle_pos, right_ankle_pos


def calculate_foot_positions(hip_center, shoulder_width, femur_type, femur_length, tibia_length, current_left_ankle,
                             current_right_ankle):
    """
    엉덩이 중심과 어깨 너비를 기준으로 발 위치 계산 (기하학적 계산 버전)

    Args:
        hip_center: [x, y, z] 엉덩이 중심 좌표 (이상적으로는 [0, y, z])
        shoulder_width: 어깨 너비
        femur_type: 대퇴골 타입 ("LONG", "AVG", "SHORT")
        femur_length: 대퇴골 길이
        tibia_length: 정강이 길이
        current_left_ankle: 현재 왼쪽 발목 좌표
        current_right_ankle: 현재 오른쪽 발목 좌표

    Returns:
        tuple: (left_ankle_pos, right_ankle_pos)
    """
    guideline = SQUAT_GUIDELINE_BY_FEMUR_TYPE.get(femur_type, SQUAT_GUIDELINE_BY_FEMUR_TYPE["AVG"])
    foot_width = shoulder_width * guideline["foot_width_ratio"]

    # 발 너비의 절반
    half_foot_width = foot_width / 2

    # 전체 다리 길이 (대퇴골 + 정강이)
    total_leg_length = femur_length + tibia_length

    # 피타고라스 정리를 사용한 발목 y 좌표 계산
    # y = hip_y - √((대퇴골 길이 + 정강이 길이)² - (발 너비/2)²)
    y_offset_squared = (total_leg_length ** 2) - (half_foot_width ** 2)

    # 음수가 되지 않도록 보호
    if y_offset_squared < 0:
        y_offset_squared = 0

    y_offset = math.sqrt(y_offset_squared)
    ankle_y = hip_center[1] + y_offset  # y축에서 +는 아래쪽

    # 왼쪽 발목 위치
    left_ankle_pos = [
        hip_center[0] - half_foot_width,  # 고관절 중심 x - 발 너비/2
        ankle_y,  # 계산된 y 좌표
        current_left_ankle['z']  # 사용자 발의 실제 z값 유지
    ]

    # 오른쪽 발목 위치
    right_ankle_pos = [
        hip_center[0] + half_foot_width,  # 고관절 중심 x + 발 너비/2
        ankle_y,  # 계산된 y 좌표
        current_right_ankle['z']  # 사용자 발의 실제 z값 유지
    ]

    return left_ankle_pos, right_ankle_pos


def calculate_knee_position_by_hip_height(
        hip_coord,
        ankle_coord,
        femur_length,
        tibia_length,
        femur_type,
        side="left"
):
    """
    엉덩이 높이에 연동하여 무릎 위치 계산

    Args:
        hip_coord: [x, y, z] 엉덩이 좌표
        ankle_coord: [x, y, z] 발목 좌표 (고정)
        femur_length: 대퇴골 길이
        tibia_length: 정강이 길이
        femur_type: 대퇴골 타입 ("LONG", "AVG", "SHORT")
        side: "left" 또는 "right"

    Returns:
        list: [x, y, z] 무릎 좌표
    """
    guideline = SQUAT_GUIDELINE_BY_FEMUR_TYPE.get(femur_type, SQUAT_GUIDELINE_BY_FEMUR_TYPE["AVG"])
    knee_angle_deg = guideline["knee_angle"]
    knee_angle_rad = degrees_to_radians(knee_angle_deg)

    hip_x, hip_y, hip_z = hip_coord
    ankle_x, ankle_y, ankle_z = ankle_coord

    # 엉덩이와 발목 사이의 높이 차이
    height_diff = hip_y - ankle_y

    # 엉덩이에서 무릎까지의 벡터 계산 (대퇴골 길이 유지)
    # 무릎은 엉덩이에서 아래쪽과 앞쪽(z축)으로 이동
    knee_y = hip_y + femur_length * math.cos(knee_angle_rad)
    knee_z = hip_z + femur_length * math.sin(knee_angle_rad)

    # 무릎의 x 좌표는 엉덩이와 발목 사이에서 적절히 계산
    # 발목에서 무릎까지의 거리가 tibia_length가 되도록 조정
    knee_x = hip_x  # 일단 x는 엉덩이와 동일하게 설정

    # 무릎-발목 거리가 정강이 길이와 맞는지 확인하고 조정
    knee_to_ankle_vec = np.array([ankle_x - knee_x, ankle_y - knee_y, ankle_z - knee_z])
    current_tibia_length = np.linalg.norm(knee_to_ankle_vec)

    if current_tibia_length > 0:
        # 정강이 길이에 맞게 스케일링
        scale_factor = tibia_length / current_tibia_length
        adjusted_vec = knee_to_ankle_vec * scale_factor

        # 발목 기준으로 무릎 위치 재계산
        knee_x = ankle_x - adjusted_vec[0]
        knee_y = ankle_y - adjusted_vec[1]
        knee_z = ankle_z - adjusted_vec[2]

    return [knee_x, knee_y, knee_z]


def clamp_hip_height(current_hip_y, femur_length, tibia_length, femur_type):
    """
    엉덩이 높이를 적절한 범위로 제한

    Args:
        current_hip_y: 현재 엉덩이 높이
        femur_length: 대퇴골 길이
        tibia_length: 정강이 길이
        femur_type: 대퇴골 타입

    Returns:
        float: 제한된 엉덩이 높이
    """
    # 최대 스쿼트 깊이 (무릎이 90도 이하로 굽혀지지 않게)
    max_squat_depth = femur_length + tibia_length * 0.7

    # 최소 스쿼트 높이 (너무 얕은 스쿼트 방지)
    min_squat_height = femur_length * 0.3

    # 엉덩이 높이 제한 적용
    if current_hip_y > max_squat_depth:
        return max_squat_depth
    elif current_hip_y < min_squat_height:
        return min_squat_height
    else:
        return current_hip_y


def calculate_hip_center(left_hip, right_hip):
    """
    좌우 엉덩이 좌표의 중심점 계산

    Args:
        left_hip: 왼쪽 엉덩이 좌표
        right_hip: 오른쪽 엉덩이 좌표

    Returns:
        list: [x, y, z] 엉덩이 중심 좌표
    """
    return [
        (left_hip['x'] + right_hip['x']) / 2,
        (left_hip['y'] + right_hip['y']) / 2,
        (left_hip['z'] + right_hip['z']) / 2
    ]