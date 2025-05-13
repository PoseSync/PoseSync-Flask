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
#--------------------------------------------------------------------------- 기존 코드(전방각 스케일링 적용 ❌)
# """
#     전방각을 유지하며 현재 팔꿈치 y 좌표에 맞는 elbow 위치(xz) 계산
# """
def calculate_elbow_position_by_forward_angle(
    shoulder_coord: list,
    arm_type: str,
    upper_arm_length: float,
    elbow_y: float,  # 사용자의 현재 팔꿈치 높이
    side: str = "left"  # "left" 또는 "right"
) -> list:
    """
    어깨 좌표와 팔꿈치 높이를 기반으로 외각(forward angle)을 유지하며 팔꿈치 좌표 계산
    """
    guideline = POSE_GUIDELINE_BY_ARM_TYPE.get(arm_type, POSE_GUIDELINE_BY_ARM_TYPE["AVG"])
    forward_rad = degrees_to_radians(guideline["forward_angle"])  # 전방각
    min_angle = guideline["elbow_min_angle"]

    shoulder_x, shoulder_y, shoulder_z = shoulder_coord
    delta_y = elbow_y - shoulder_y

    # ✅ elbow_min_angle 유지 가능한 최소 팔꿈치 높이 계산
    min_rad = degrees_to_radians(min_angle)
    min_delta_y = math.cos(min_rad) * upper_arm_length

    # ✅ 손목이 어깨보다 아래에 있고, min_angle보다 팔꿈치가 너무 낮은 경우 보정
    if delta_y < min_delta_y:
        elbow_y = shoulder_y + min_delta_y
        delta_y = elbow_y - shoulder_y

    # xz 평면 투영 거리 계산
    proj_length = math.sqrt(max(upper_arm_length ** 2 - delta_y ** 2, 0))

    # 어깨로부터 축방향으로 이동한 거리
    dx = math.cos(forward_rad) * proj_length
    dz = math.sin(forward_rad) * proj_length

    # 왼팔/오른팔에 따라 정확히 대칭되게 처리
    if side == "right":
        # 오른팔은 dx를 양수로 (또는 다른 방향 지정)
        pass
    else:  # side == "left"
        # 왼팔은 dx를 음수로 (또는 다른 방향 지정)
        dx = -dx
        # 필요하다면 dz도 적절히 조정
        # dz = -dz  # 좌우 대칭이 필요하면 이 부분도 추가

    return [shoulder_x + dx, elbow_y, shoulder_z + dz]
#--------------------------------------------------------------------------- 기존 코드(전방각 스케일링 적용 ❌)
# def calculate_elbow_position_by_forward_angle(
#         shoulder_coord: list,
#         arm_type: str,
#         upper_arm_length: float,
#         elbow_y: float,  # 사용자의 현재 팔꿈치 높이
#         side: str = "left"  # "left" 또는 "right"
# ) -> list:
#     """
#     어깨 좌표와 팔꿈치 높이를 기반으로 외각(forward angle)을 유지하며 팔꿈치 좌표 계산
#     min_height_diff 높이에서 최대 전방각을 가지고, 팔꿈치가 올라갈수록 전방각 감소
#     """
#     guideline = POSE_GUIDELINE_BY_ARM_TYPE.get(arm_type, POSE_GUIDELINE_BY_ARM_TYPE["AVG"])
#     base_forward_angle = guideline["forward_angle"]  # 기본 전방각
#     min_elbow_angle = guideline["elbow_min_angle"]
#
#     shoulder_x, shoulder_y, shoulder_z = shoulder_coord
#     elbow_shoulder_height_diff = elbow_y - shoulder_y  # 양수면 팔꿈치가 어깨보다 아래에 있음
#
#     # 최소 팔꿈치 각도를 유지하기 위한 최소 높이 차이 계산
#     min_angle_radians = degrees_to_radians(min_elbow_angle)
#     min_height_diff = math.cos(min_angle_radians) * upper_arm_length
#
#     # 팔꿈치가 너무 낮아 최소 각도보다 작을 경우 높이 보정
#     if elbow_shoulder_height_diff < min_height_diff:
#         elbow_y = shoulder_y + min_height_diff
#         elbow_shoulder_height_diff = elbow_y - shoulder_y
#
#     # min_height_diff 이상일 때는 기본 전방각 사용, 이하일 때 점점 감소
#     # 즉, 팔꿈치가 어깨보다 높아질수록 전방각 감소
#
#     # 팔꿈치가 올라간 정도 계산
#     # min_height_diff가 기준점(팔꿈치 최소 높이)
#     # min_height_diff에서 팔꿈치가 얼마나 올라갔는지 계산
#     elbow_raise_amount = min_height_diff - elbow_shoulder_height_diff
#
#     # 최대 올림 가능 범위 계산 (완전히 수직으로 올렸을 때)
#     # min_height_diff에서 최대 위치(-upper_arm_length) 사이의 범위
#     max_raise_range = min_height_diff + upper_arm_length
#
#     # 올림 비율 계산 (0: 최소 높이, 1: 최대 올림)
#     # 음수가 되지 않도록 max 사용
#     elbow_raise_ratio = max(0, elbow_raise_amount) / max_raise_range
#
#     # 전방각 조정: 팔꿈치가 올라갈수록 전방각이 선형적으로 감소
#     adjusted_forward_angle = base_forward_angle * (1.0 - elbow_raise_ratio)
#
#     # 전방각이 너무 작아지지 않도록 최소값 설정
#     min_forward_angle = 2.0  # 최소 2도의 전방각 유지
#     adjusted_forward_angle = max(adjusted_forward_angle, min_forward_angle)
#
#     forward_angle_radians = degrees_to_radians(adjusted_forward_angle)
#
#     # 상완 길이를 유지하면서 xz 평면에 투영된 거리 계산
#     horizontal_projection = math.sqrt(max(upper_arm_length ** 2 - elbow_shoulder_height_diff ** 2, 0))
#
#     # 어깨로부터 팔꿈치까지의 x, z 방향 거리 계산
#     x_offset = math.cos(forward_angle_radians) * horizontal_projection
#     z_offset = math.sin(forward_angle_radians) * horizontal_projection
#
#     # 왼팔/오른팔에 따라 대칭되게 처리
#     if side == "left":
#         # 왼팔은 x 방향을 반대로
#         x_offset = -x_offset
#         z_offset = -z_offset  # 필요시 주석 해제
#
#     # 최종 팔꿈치 좌표 계산
#     elbow_x = shoulder_x + x_offset
#     elbow_z = shoulder_z + z_offset
#
#     return [elbow_x, elbow_y, elbow_z]


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