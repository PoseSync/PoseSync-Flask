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
        torso_arm_angle: float,
        upper_arm_length: float,
        side: str = "right"
) -> list:
    """
    바벨컬을 위한 팔꿈치 위치 계산 (시뮬레이션 버전 17 로직)
    - 팔꿈치 높이를 상완 길이와 토르소 각도로 자동 계산
    - 물리적으로 정확한 상완 벡터 유지

    Args:
        shoulder_coord: 어깨 좌표 [x, y, z]
        hip_coord: 엉덩이 좌표 [x, y, z] (현재 미사용, 호환성 유지)
        torso_arm_angle: 토르소 각도 (도 단위)
        upper_arm_length: 상완 길이
        side: 팔 방향 ("left" or "right")

    Returns:
        list: 계산된 팔꿈치 좌표 [x, y, z]
    """

    # 토르소 각도를 라디안으로 변환
    angle_rad = math.radians(torso_arm_angle)

    shoulder_x, shoulder_y, shoulder_z = shoulder_coord

    # 팔꿈치 높이 계산: 어깨에서 상완 길이만큼 아래로 + 토르소 각도 보정
    # 수직 성분 = 상완길이 × cos(토르소각도)
    vertical_drop = upper_arm_length * math.cos(angle_rad)
    elbow_y = shoulder_y + vertical_drop

    # X 오프셋 (팔꿈치가 몸통에 너무 붙지 않도록)
    x_offset = 0.01
    elbow_x = shoulder_x + x_offset

    # Z 좌표: 토르소 각도에 따라 앞쪽으로 조정
    # 전진 성분 = 상완길이 × sin(토르소각도)
    forward_projection = upper_arm_length * math.sin(angle_rad)
    elbow_z = shoulder_z + forward_projection

    return [elbow_x, elbow_y, elbow_z]


# 사용 예시
if __name__ == "__main__":
    # 테스트 케이스
    shoulder_coord = [0.2, 0.0, 0.0]  # 오른쪽 어깨
    hip_coord = [0.15, 0.6, 0.0]  # 오른쪽 엉덩이
    torso_arm_angle = 5.0  # 5도 전방 각도
    upper_arm_length = 0.3  # 상완 길이

    elbow_pos = calculate_elbow_position_for_barbell_curl(
        shoulder_coord, hip_coord, torso_arm_angle, upper_arm_length, "right"
    )

    print(f"어깨 위치: {shoulder_coord}")
    print(f"토르소 각도: {torso_arm_angle}°")
    print(f"상완 길이: {upper_arm_length}")
    print(f"계산된 팔꿈치 위치: {elbow_pos}")
    print(f"팔꿈치 높이 변화: {elbow_pos[1] - shoulder_coord[1]:.3f}")
    print(f"팔꿈치 전진 거리: {elbow_pos[2] - shoulder_coord[2]:.3f}")

    # 각도별 비교
    print("\n각도별 팔꿈치 위치 비교:")
    for angle in [0, 5, 10, 15, 20]:
        elbow = calculate_elbow_position_for_barbell_curl(
            shoulder_coord, hip_coord, angle, upper_arm_length, "right"
        )
        print(f"{angle:2d}°: Y={elbow[1]:.3f}, Z={elbow[2]:.3f}")

"""
시뮬레이션 버전 17의 핵심 로직:

1. 팔꿈치 높이 자동 계산:
   elbow_y = shoulder_y + upper_arm_length × cos(torso_angle)

2. 팔꿈치 전진 거리:
   elbow_z = shoulder_z + upper_arm_length × sin(torso_angle)

3. 물리적 정확성:
   - 어깨-팔꿈치 거리가 항상 upper_arm_length로 유지됨
   - 토르소 각도에 따라 수직/수평 성분이 자동 분배됨

4. 각도 의미:
   - 0°: 팔이 완전히 수직으로 내려감
   - 15°: 팔꿈치가 앞으로 나가고 높이도 약간 올라감
   - 90°: 팔이 완전히 수평 (비현실적)
"""


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