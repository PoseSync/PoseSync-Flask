import math, numpy as np

from app.util.math_util import normalize_vector, vector_angle_deg

# 상완 타입별
POSE_GUIDELINE_BY_ARM_TYPE = {
    "LONG": {
        "forward_angle": 12.5,    # 전방각(고정)
        "elbow_min_angle": 100.0   # 팔꿈치 최소각도
    },
    "AVG": {
        "forward_angle": 10.5,
        "elbow_min_angle": 90
    },
    "SHORT": {
        "forward_angle": 7.5,
        "elbow_min_angle": 80
    }
}

def degrees_to_radians(deg):
    return deg * math.pi / 180

#--------------------------------------------------------------------------- 기존 코드(전방각 스케일링 적용⭕ 🔽🔽🔽)
def calculate_elbow_position_by_forward_angle(
        shoulder_coord: list,
        arm_type: str,
        upper_arm_length: float,
        elbow_y: float,                 # 사용자의 현재 팔꿈치 높이
        side: str = "left"              # "left" 또는 "right"
) -> list:
    """
    어깨 좌표와 팔꿈치 높이를 기반으로 전방각(forward angle)을 유지하며 팔꿈치 좌표 계산
    - mediaPipe Landmarks 좌표를(0~1범위 화면기준) 서버에서 고관절 중심점 기준 (-1~1)범위 좌표계로 정규화하여 사용
    - min_height_diff(=최소 팔꿈치-어깨 높이차) 이하에서는 전방각이 점차 줄어든다.
    """
    guideline           = POSE_GUIDELINE_BY_ARM_TYPE.get(arm_type,
                                                         POSE_GUIDELINE_BY_ARM_TYPE["AVG"])
    base_forward_angle  = guideline["forward_angle"]     # 기본 전방각(°)
    min_elbow_angle     = guideline["elbow_min_angle"]   # 팔꿈치 최소 각도(°)

    shoulder_x, shoulder_y, shoulder_z = shoulder_coord

    # ────────────────────────────────────────────────────
    # 1. 팔꿈치-어깨 높이 차 계산(+면 팔꿈치가 어깨보다 아래)
    elbow_shoulder_height_diff = elbow_y - shoulder_y
    print(f'상완 길이 {upper_arm_length} 팔꿈치 y {elbow_y} 어깨 y : {shoulder_y}')
    # 2. '최소 팔꿈치 각도'를 만족하기 위한 최소 높이차
    min_angle_radians  = math.radians(min_elbow_angle)
    min_height_diff    = math.cos(min_angle_radians) * upper_arm_length

    # 3. 팔꿈치가 너무 낮으면 보정(팔꿈치 최소 각도 유지)
    if elbow_shoulder_height_diff < min_height_diff:
        elbow_y = shoulder_y + min_height_diff
        elbow_shoulder_height_diff = elbow_y - shoulder_y
    # ────────────────────────────────────────────────────

    # 4. 올림(raise) 비율: min_height_diff 에서 ‘얼마나 더 위로’ 올렸는가
    # ✅ 수정
    elbow_raise_amount = max(0.0, elbow_shoulder_height_diff - min_height_diff)
    max_raise_range = upper_arm_length - min_height_diff
    elbow_raise_ratio = elbow_raise_amount / max_raise_range  # 0~1

    # 5. 전방각 보정 : 팔꿈치가 올라갈수록 전방각 감소(선형)
    adjusted_forward_angle = base_forward_angle * (1.0 - elbow_raise_ratio)

    # 6. 전방각 하한값(0° 이하로는 작아지지 않게)
    adjusted_forward_angle = max(adjusted_forward_angle, 0.0)
    forward_angle_radians  = math.radians(adjusted_forward_angle)

    # 7. x-z 평면 투영 길이(수평 성분) = √(L² − Δy²)
    horizontal_projection = math.sqrt(max(
        upper_arm_length ** 2 - elbow_shoulder_height_diff ** 2,
        0.0
    ))

    # 8. x / z 오프셋
    x_offset = math.cos(forward_angle_radians) * horizontal_projection
    z_offset = math.sin(forward_angle_radians) * horizontal_projection

    print(
        f'x_offset : {x_offset} z_offset : {z_offset} horizontal_projection : {horizontal_projection} elbow_shoulder_height_diff : {elbow_shoulder_height_diff}')

    # 왼팔이면 x 반전(대칭)
    if side == "left":
        x_offset = -x_offset
        # 필요하면 z_offset 도 반전 가능
        # z_offset = -z_offset

    # 9. 최종 팔꿈치 좌표
    elbow_x = shoulder_x + x_offset
    elbow_z = shoulder_z + z_offset

    return [elbow_x, elbow_y, elbow_z]


def adjust_wrist_direction_to_preserve_min_angle(
        shoulder_coord: list,
        elbow_coord: list,
        forearm_length: float,
        arm_type: str,
        side: str = "left"  # "left" 또는 "right"
) -> list:
    """
    팔꿈치에서 수직으로 위로 올라가는 방향으로 손목 위치를 계산
    """
    # 팔꿈치 좌표
    elbow = np.array(elbow_coord)

    # 수직 방향(y축 양의 방향)으로 forearm_length만큼 이동
    vertical_dir = np.array([0, 1, 0])  # y축은 아래가 양수이므로 -1 사용

    # 손목 위치 = 팔꿈치 + 수직방향 * 전완 길이
    wrist = elbow + vertical_dir * forearm_length

    return wrist.tolist()