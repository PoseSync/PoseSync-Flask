import math, numpy as np

from app.util.math_util import normalize_vector, vector_angle_deg

# 상완 타입별
POSE_GUIDELINE_BY_ARM_TYPE = {
    "LONG": {
        "forward_angle": 17.5,    # 전방각(고정)
        "elbow_min_angle": 87.5   # 팔꿈치 최소각도
    },
    "AVG": {
        "forward_angle": 14.5,
        "elbow_min_angle": 90.0
    },
    "SHORT": {
        "forward_angle": 12.5,
        "elbow_min_angle": 90.0
    }
}

def degrees_to_radians(deg):
    return deg * math.pi / 180

"""
    전방각을 유지하며 현재 팔꿈치 y 좌표에 맞는 elbow 위치(xz) 계산
"""
def calculate_elbow_position_by_forward_angle(
    shoulder_coord: list,
    arm_type: str,
    upper_arm_length: float,
    elbow_y: float  # 사용자의 현재 팔꿈치 높이
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
        elbow_y = shoulder_y + min_delta_y   #원래는 사용자의 팔꿈치 y 였지만 이제 가이드라인 좌표의 y가 됨
        delta_y = elbow_y - shoulder_y

    # xz 평면 투영 거리 계산
    proj_length = math.sqrt(max(upper_arm_length ** 2 - delta_y ** 2, 0))

    # 어깨로부터 축방향으로 이동한 거리
    dx = math.cos(forward_rad) * proj_length
    dz = math.sin(forward_rad) * proj_length

    if shoulder_x < 0:
        dx = -dx

    return [shoulder_x + dx, elbow_y, shoulder_z + dz]

# def calculate_elbow_position_by_forward_angle(
#     shoulder_coord: list,
#     arm_type: str,
#     upper_arm_length: float,
#     elbow_y: float  # 사용자의 현재 팔꿈치 높이
# ) -> list:
#     """
#     어깨 좌표와 팔꿈치 높이를 기반으로 외각(forward angle)을 유지하며 팔꿈치 좌표 계산
#     """
#     guideline = POSE_GUIDELINE_BY_ARM_TYPE.get(arm_type, POSE_GUIDELINE_BY_ARM_TYPE[arm_type])
#     forward_rad = degrees_to_radians(guideline["forward_angle"])  # 전방각
#
#     shoulder_x, shoulder_y, shoulder_z = shoulder_coord
#     delta_y = elbow_y - shoulder_y #어깨와 팔꿈치 사이의 높이차이
#
#     # xz 평면 투영 거리 계산
#     proj_length = math.sqrt(max(upper_arm_length ** 2 - delta_y ** 2, 0))
#
#     # 어깨로부터 축방향으로 이동한 거리
#     dx = math.cos(forward_rad) * proj_length
#     dz = math.sin(forward_rad) * proj_length
#
#     # 왼팔/오른팔 여부는 shoulder_x 부호로 판단
#     if shoulder_x < 0:
#         dx = -dx
#
#     return [shoulder_x + dx, elbow_y, shoulder_z + dz]


#팔꿈치는 그대로, 손목 방향을 벌려서 팔꿈치 각도를 만족하도록
def adjust_wrist_direction_to_preserve_min_angle(
    shoulder_coord: list,
    elbow_coord: list,
    forearm_length: float,
    arm_type: str
) -> list:
    """
    팔꿈치는 고정한 채,
    elbow_min_angle을 만족하도록 손목 방향을 보정하여 전완 방향을 회전
    """
    guideline = POSE_GUIDELINE_BY_ARM_TYPE.get(arm_type, POSE_GUIDELINE_BY_ARM_TYPE["AVG"])
    min_angle = guideline["elbow_min_angle"]

    shoulder = np.array(shoulder_coord)
    elbow = np.array(elbow_coord)
    upper_vec = elbow - shoulder
    upper_unit = normalize_vector(upper_vec)

    forearm_dir = np.array([0, 1, 0]) # 바닥면(어깨)에 수직을 이루는 전완골 벡터

    angle = vector_angle_deg(upper_unit, forearm_dir)

    if angle < min_angle:
        angle_rad = degrees_to_radians(min_angle)
        xz_proj = np.array([upper_unit[0], 0, upper_unit[2]]) #투영한 결과가 거의 (0,0,0)에 가깝다면 → xz 평면에 벡터가 없음 = 거의 수직
        if np.linalg.norm(xz_proj) < 1e-6:
            perp_vec = np.array([1, 0, 0])
        else:
            perp_vec = np.cross(xz_proj, [0, 1, 0])
        perp_unit = normalize_vector(perp_vec)

        new_dir = (
            math.cos(angle_rad) * upper_unit + math.sin(angle_rad) * perp_unit
        )
        forearm_dir = normalize_vector(new_dir)

    wrist = elbow + forearm_dir * forearm_length
    return wrist.tolist()



# 손목 방향은 y+ 수직, 팔꿈치 y좌표만 제한하는 방식

# def clamp_elbow_y_for_min_angle(
#     shoulder_coord: list,
#     initial_elbow_coord: list,
#     forearm_length: float,
#     arm_type: str
# ) -> list:
#     """
#     손목 방향은 항상 y+ 수직으로 유지,
#     elbow_min_angle을 만족하지 못하면 팔꿈치의 y값을 제한하여
#     더 이상 내려가지 않도록 보정
#     """
#     guideline = POSE_GUIDELINE_BY_ARM_TYPE.get(arm_type, POSE_GUIDELINE_BY_ARM_TYPE["AVG"])
#     min_angle = guideline["elbow_min_angle"]
#
#     shoulder = np.array(shoulder_coord)
#     elbow = np.array(initial_elbow_coord)
#
#     upper_vec = elbow - shoulder
#     upper_unit = normalize_vector(upper_vec)
#
#     forearm_dir = np.array([0, 1, 0])
#     angle = vector_angle_deg(upper_unit, forearm_dir)
#
#     if angle < min_angle:
#         arm_len = np.linalg.norm(upper_vec)
#         min_dy = arm_len * math.cos(degrees_to_radians(min_angle))
#         elbow[1] = shoulder[1] + min_dy
#
#     return elbow.tolist()


"""
벤치프레스에 적용가능
"""
# """
# 팔꿈치 최소각도를 검사하며 이를 기반으로 손목위치 조절
# """
# def calculate_wrist_position_correct_angle(
#     elbow_coord: list, #팔꿈치 좌표
#     shoulder_line_vec: np.ndarray, # 어깨벡터
#     forearm_length: float, # 전완근 길이 -> 손목좌표 계산에 사용
#     side: str # left right
# ) -> list:
#     """
#     어깨 라인과 90도 각도를 이루는 방향으로 forearm_length만큼 뻗어 손목 위치를 계산한다.
#     """
# 
#     # 어깨 라인을 단위 벡터로 정규화
#     shoulder_unit = normalize_vector(shoulder_line_vec)
# 
#     # 전완 방향: 어깨선에 수직한 방향 (y축은 유지, 수평 기준)
#     # 왼팔이면 (-z, 0, x), 오른팔이면 (z, 0, -x)
#     if side == "left":
#         forearm_dir = np.array([-shoulder_unit[2], 0, shoulder_unit[0]])
#     else:  # side == "right"
#         forearm_dir = np.array([shoulder_unit[2], 0, -shoulder_unit[0]])
#     forearm_dir = normalize_vector(forearm_dir)
# 
#     # 손목 위치 = 팔꿈치 + 전완방향 * 길이
#     wrist_pos = np.array(elbow_coord) + forearm_dir * forearm_length
#     return wrist_pos.tolist()

