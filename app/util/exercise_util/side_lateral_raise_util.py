import math
import numpy as np
from app.util.math_util import normalize_vector, vector_angle_deg

# 상완 타입별 사이드 레터럴 레이즈 가이드라인
LATERAL_RAISE_GUIDELINE_BY_ARM_TYPE = {
    "LONG": {
        "elbow_flexion_angle": 17.5,  # 팔꿈치 굴곡 각도
        "max_raise_y_offset": -0.05,  # 최대 거상 높이 (어깨 대비 오프셋)
        "torso_lean_angle": 10.0,     # 상체 기울기
        "min_abduction_angle": 15.0   # 최소 외전 각도
    },
    "AVG": {
        "elbow_flexion_angle": 12.5,
        "max_raise_y_offset": -0.04,
        "torso_lean_angle": 10.0,
        "min_abduction_angle": 20.0
    },
    "SHORT": {
        "elbow_flexion_angle": 7.5,
        "max_raise_y_offset": -0.03,
        "torso_lean_angle": 10.0,
        "min_abduction_angle": 25.0
    }
}


def calculate_elbow_position_for_lateral_raise(
        shoulder_coord: list,
        current_elbow_coord: list,
        arm_type: str,
        upper_arm_length: float,
        side: str = "left"
) -> list:
    """
    사이드 레터럴 레이즈를 위한 팔꿈치 위치 계산
    
    🔑 정변환 좌표계 이해:
    - 원점: 고관절 중심 (0,0,0)
    - Y축: 고관절→어깨 방향이 양수 (위쪽이 양수)
    - X축: 왼쪽이 음수, 오른쪽이 양수
    - Z축: 앞쪽이 음수, 뒤쪽이 양수
    """
    guideline = LATERAL_RAISE_GUIDELINE_BY_ARM_TYPE.get(arm_type, LATERAL_RAISE_GUIDELINE_BY_ARM_TYPE["AVG"])
    elbow_flexion_angle = guideline["elbow_flexion_angle"]
    max_raise_y_offset = guideline["max_raise_y_offset"]
    min_abduction_angle = guideline["min_abduction_angle"]

    shoulder_x, shoulder_y, shoulder_z = shoulder_coord
    current_elbow_x, current_elbow_y, current_elbow_z = current_elbow_coord

    # 현재 팔의 외전 각도 계산 (어깨에서 팔꿈치로의 벡터와 Y축의 각도)
    current_arm_vector = np.array([
        current_elbow_x - shoulder_x,
        current_elbow_y - shoulder_y,
        current_elbow_z - shoulder_z
    ])
    
    # Y축 벡터 (수직 아래 방향)
    vertical_vector = np.array([0, -1, 0])
    
    # 현재 외전 각도 계산
    current_abduction_angle = vector_angle_deg(current_arm_vector, vertical_vector)
    
    # 최소 외전 각도 보정
    if current_abduction_angle < min_abduction_angle:
        abduction_angle = min_abduction_angle
    else:
        abduction_angle = current_abduction_angle

    # 외전 각도를 라디안으로 변환
    abduction_rad = math.radians(abduction_angle)

    # 팔꿈치 높이 계산 (어깨보다 아래에 위치)
    # max_raise_y_offset을 고려하여 최대 높이 제한
    elbow_y_from_abduction = shoulder_y - upper_arm_length * math.cos(abduction_rad)
    max_elbow_y = shoulder_y + max_raise_y_offset
    elbow_y = max(elbow_y_from_abduction, max_elbow_y)

    # 좌우 구분에 따른 X 위치 계산
    side_multiplier = -1 if side == "left" else 1
    
    # 외전 시 X축으로 팔이 벌어짐
    elbow_x = shoulder_x + side_multiplier * upper_arm_length * math.sin(abduction_rad)

    # Z축 위치 (약간 앞으로)
    elbow_z = shoulder_z - 0.05  # 약간 앞으로 내밀어서 자연스러운 자세

    print(f'{side} 팔 - 외전각도: {abduction_angle:.1f}°, 팔꿈치 위치: ({elbow_x:.3f}, {elbow_y:.3f}, {elbow_z:.3f})')

    return [elbow_x, elbow_y, elbow_z]


def calculate_wrist_position_for_lateral_raise(
        shoulder_coord: list,
        elbow_coord: list,
        current_wrist_coord: list,
        forearm_length: float,
        arm_type: str,
        side: str = "left"
) -> list:
    """
    사이드 레터럴 레이즈를 위한 손목 위치 계산
    - 팔꿈치에서 설정된 굴곡 각도로 전완 위치 결정
    - 사용자의 현재 움직임을 어느 정도 반영
    """
    guideline = LATERAL_RAISE_GUIDELINE_BY_ARM_TYPE.get(arm_type, LATERAL_RAISE_GUIDELINE_BY_ARM_TYPE["AVG"])
    elbow_flexion_angle = guideline["elbow_flexion_angle"]

    shoulder_x, shoulder_y, shoulder_z = shoulder_coord
    elbow_x, elbow_y, elbow_z = elbow_coord
    current_wrist_x, current_wrist_y, current_wrist_z = current_wrist_coord

    # 상완 벡터 (어깨 → 팔꿈치)
    upper_arm_vector = np.array([
        elbow_x - shoulder_x,
        elbow_y - shoulder_y,
        elbow_z - shoulder_z
    ])
    upper_arm_vector = normalize_vector(upper_arm_vector)

    # 현재 전완 벡터 (팔꿈치 → 손목)
    current_forearm_vector = np.array([
        current_wrist_x - elbow_x,
        current_wrist_y - elbow_y,
        current_wrist_z - elbow_z
    ])

    # 상완과 전완 사이의 현재 각도
    current_elbow_angle = vector_angle_deg(upper_arm_vector, current_forearm_vector)

    # 팔꿈치 굴곡 각도 적용
    # 현재 각도가 너무 작으면 최소 굴곡각으로 보정
    if current_elbow_angle < elbow_flexion_angle:
        target_angle = elbow_flexion_angle
    else:
        # 사용자의 자연스러운 움직임 허용 (최대 30도까지)
        target_angle = min(current_elbow_angle, 30.0)

    target_angle_rad = math.radians(target_angle)

    # 전완 방향 벡터 계산
    # 레터럴 레이즈에서는 팔꿈치에서 약간 아래쪽으로 굽어짐
    
    # 상완 벡터를 기준으로 회전축 계산 (Z축 방향)
    rotation_axis = np.array([0, 0, 1])  # Z축 기준 회전
    
    # 좌우에 따른 회전 방향 조정
    side_multiplier = 1 if side == "left" else -1
    
    # 팔꿈치 굴곡을 고려한 전완 방향
    # 상완 벡터에서 약간 아래쪽으로 굽힘
    forearm_direction = upper_arm_vector.copy()
    
    # Y 성분을 줄여서 아래쪽으로 굽힘
    forearm_direction[1] -= math.sin(target_angle_rad) * 0.5
    
    # X 성분을 조정하여 자연스러운 굽힘
    forearm_direction[0] += side_multiplier * math.sin(target_angle_rad) * 0.3
    
    forearm_direction = normalize_vector(forearm_direction)

    # 손목 위치 = 팔꿈치 + 전완방향 * 전완길이
    wrist_pos = np.array(elbow_coord) + forearm_direction * forearm_length

    print(f'{side} 팔 - 팔꿈치 굽힘각도: {target_angle:.1f}°, 손목 위치: ({wrist_pos[0]:.3f}, {wrist_pos[1]:.3f}, {wrist_pos[2]:.3f})')

    return wrist_pos.tolist()


def calculate_lateral_raise_progression(
        shoulder_coord: list,
        current_elbow_height: float,
        arm_type: str,
        upper_arm_length: float
) -> float:
    """
    현재 팔꿈치 높이를 기반으로 레터럴 레이즈 진행도 계산
    반환값: 0.0 (시작) ~ 1.0 (최대 거상)
    """
    guideline = LATERAL_RAISE_GUIDELINE_BY_ARM_TYPE.get(arm_type, LATERAL_RAISE_GUIDELINE_BY_ARM_TYPE["AVG"])
    max_raise_y_offset = guideline["max_raise_y_offset"]
    
    shoulder_y = shoulder_coord[1]
    max_elbow_y = shoulder_y + max_raise_y_offset
    min_elbow_y = shoulder_y - upper_arm_length  # 팔이 완전히 내려간 상태
    
    # 진행도 계산
    if current_elbow_height <= min_elbow_y:
        return 0.0
    elif current_elbow_height >= max_elbow_y:
        return 1.0
    else:
        return (current_elbow_height - min_elbow_y) / (max_elbow_y - min_elbow_y)