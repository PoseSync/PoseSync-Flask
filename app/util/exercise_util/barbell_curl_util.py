import math
import numpy as np
from app.util.math_util import normalize_vector, vector_angle_deg

# 상완 타입별 바벨컬 가이드라인
BARBELL_CURL_GUIDELINE_BY_ARM_TYPE = {
    "LONG": {
        "grip_width_ratio": 1.1,  # 어깨 너비의 1.1배
        "min_forearm_angle": 30.0,  # 전완-상완 최소 각도
        "torso_arm_angle": 0.0  # 몸통-상완 각도
    },
    "AVG": {
        "grip_width_ratio": 1.05,
        "min_forearm_angle": 25.0,
        "torso_arm_angle": 5.0
    },
    "SHORT": {
        "grip_width_ratio": 1.0,
        "min_forearm_angle": 20.0,
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

    🔑 정변환 좌표계 이해:
    - 원점: 고관절 중심 (0,0,0)
    - Y축: 고관절→어깨 방향이 양수 (위쪽이 양수)
    - 어깨가 Y 양수 영역, 팔꿈치는 어깨보다 아래이므로 Y값이 더 작아야 함
    """
    guideline = BARBELL_CURL_GUIDELINE_BY_ARM_TYPE.get(arm_type)
    torso_arm_angle = guideline["torso_arm_angle"]

    shoulder_x, shoulder_y, shoulder_z = shoulder_coord

    # 토르소 각도를 라디안으로 변환
    angle_rad = math.radians(torso_arm_angle)

    # ✅ 수정: 정변환에서 Y축 위쪽이 양수이므로
    # 팔꿈치가 어깨보다 아래에 있으려면 Y값이 더 작아야 함
    elbow_y = shoulder_y - upper_arm_length * math.cos(angle_rad)

    # Z축: 바벨컬에서는 팔을 앞으로 약간 내밀다가 구부림
    elbow_z = shoulder_z + upper_arm_length * math.sin(angle_rad)

    x_offset = -0.02
    # X 좌표: 어깨와 동일한 위치 유지
    elbow_x = shoulder_x + x_offset

    print(f"[{side}] 바벨컬 팔꿈치 계산 (정변환 좌표계):")
    print(f"[{side}] 어깨 Y: {shoulder_y:.3f} (위쪽) → 팔꿈치 Y: {elbow_y:.3f} (아래쪽)")
    print(f"[{side}] Y 변화: {elbow_y - shoulder_y:.3f} (음수=아래로)")
    print(f"[{side}] 토르소 각도: {torso_arm_angle}°, Z 전진: +{upper_arm_length * math.sin(angle_rad):.3f}")

    return [elbow_x, elbow_y, -elbow_z]


def calculate_wrist_position_for_barbell_curl(
        elbow_coord: list,
        current_wrist_coord: list,
        shoulder_coord: list,  # 어깨 좌표
        forearm_length: float,
        arm_type: str,
        side: str = "right"
) -> list:
    """
    바벨컬을 위한 손목 위치 계산
    - 사용자의 현재 손목 높이와 각도를 반영
    - 최소 각도만 보정하고 나머지는 사용자 움직임 따라감
    """
    guideline = BARBELL_CURL_GUIDELINE_BY_ARM_TYPE.get(arm_type, BARBELL_CURL_GUIDELINE_BY_ARM_TYPE["AVG"])
    grip_width_ratio = guideline["grip_width_ratio"]
    min_forearm_angle = guideline["min_forearm_angle"]

    elbow_x, elbow_y, elbow_z = elbow_coord
    current_wrist_x, current_wrist_y, current_wrist_z = current_wrist_coord
    shoulder_x, shoulder_y, shoulder_z = shoulder_coord

    # 현재 전완 벡터 (팔꿈치 → 손목)
    forearm_vector = np.array([
        current_wrist_x - elbow_x,
        current_wrist_y - elbow_y,
        current_wrist_z - elbow_z
    ])

    # ✅ 정변환 좌표계에서 아래 방향은 Y 양수
    vertical_down_vector = np.array([0, 1, 0])

    # 현재 전완 각도 계산
    current_angle = vector_angle_deg(forearm_vector, vertical_down_vector)

    # ✅ 최소 각도 체크 및 보정 (사용자가 너무 구부리지 않도록)
    if current_angle < min_forearm_angle:
        print(f"[{side}] 최소 각도 보정: {current_angle:.1f}° → {min_forearm_angle}°")
        angle_rad = math.radians(min_forearm_angle)
    else:
        # 사용자의 현재 각도 사용 (자연스러운 움직임)
        angle_rad = math.radians(current_angle)

    # ✅ 손목 Y 좌표: 팔꿈치에서 전완 길이만큼 아래
    # 정변환 좌표계에서 Y+가 아래쪽이므로 +
    wrist_y = elbow_y + forearm_length * math.cos(angle_rad)

    # ✅ 손목 Z 좌표: 바벨컬에서는 몸 쪽으로 당겨짐
    # 각도가 클수록 더 많이 구부러져서 몸 쪽으로
    wrist_z = elbow_z - forearm_length * math.sin(angle_rad)

    # ✅ 손목 X 좌표: 어깨 X 좌표에 그립 비율 적용 (자동 좌우 대칭)
    wrist_x = shoulder_x * grip_width_ratio

    print(f"[{side}] 바벨컬 손목 계산 (동적 높이):")
    print(f"[{side}] 현재 각도: {current_angle:.1f}°, 사용 각도: {math.degrees(angle_rad):.1f}°")
    print(f"[{side}] 어깨 X: {shoulder_x:.3f} → 손목 X: {wrist_x:.3f} (×{grip_width_ratio:.2f})")
    print(f"[{side}] 팔꿈치 Y: {elbow_y:.3f} → 손목 Y: {wrist_y:.3f}")

    return [wrist_x, wrist_y, wrist_z]



def create_symmetric_arm_positions(
        right_elbow_pos: list,
        right_wrist_pos: list,
        body_center_x: float = 0.0
) -> tuple:
    """
    오른팔 위치를 기준으로 왼팔 대칭 위치 생성
    정변환 좌표계에서는 원점이 고관절 중심
    """
    # 왼팔 팔꿈치: X 좌표만 대칭
    left_elbow_pos = [
        body_center_x - (right_elbow_pos[0] - body_center_x),  # X 대칭
        right_elbow_pos[1],  # Y 동일 (높이)
        right_elbow_pos[2]  # Z 동일 (앞뒤)
    ]

    # 왼팔 손목: X 좌표만 대칭
    left_wrist_pos = [
        body_center_x - (right_wrist_pos[0] - body_center_x),  # X 대칭
        right_wrist_pos[1],  # Y 동일 (높이)
        right_wrist_pos[2]  # Z 동일 (앞뒤)
    ]

    print(f"대칭 생성 (정변환 좌표계):")
    print(f"오른팔 → 왼팔 팔꿈치: {right_elbow_pos} → {left_elbow_pos}")
    print(f"오른팔 → 왼팔 손목: {right_wrist_pos} → {left_wrist_pos}")

    return left_elbow_pos, left_wrist_pos