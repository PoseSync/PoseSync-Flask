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
       current_elbow_coord: list,  # 현재 사용자 팔꿈치 좌표
       arm_type: str,
       upper_arm_length: float,
       side: str = "left"
) -> list:
   """
   어깨 좌표와 팔꿈치 높이를 기반으로 전방각(forward angle)을 유지하며 팔꿈치 좌표 계산
   - mediaPipe Landmarks 좌표를(0~1범위 화면기준) 서버에서 고관절 중심점 기준 (-1~1)범위 좌표계로 정규화하여 사용
   - min_height_diff(=최소 팔꿈치-어깨 높이차) 이하에서는 전방각이 점차 줄어든다.
   """
   guideline           = POSE_GUIDELINE_BY_ARM_TYPE.get(arm_type, POSE_GUIDELINE_BY_ARM_TYPE["AVG"])
   base_forward_angle  = guideline["forward_angle"]     # 기본 전방각(°)
   min_elbow_angle     = guideline["elbow_min_angle"]   # 팔꿈치 최소 각도(°)

   shoulder_x, shoulder_y, shoulder_z = shoulder_coord

   # 현재 팔꿈치 좌표 분해
   current_elbow_x, current_elbow_y, current_elbow_z = current_elbow_coord

   # 실제 상완 벡터 (어깨 → 현재 팔꿈치)
   upper_arm_vector = np.array([
       current_elbow_x - shoulder_x,
       current_elbow_y - shoulder_y,
       current_elbow_z - shoulder_z
   ])

   # xz 평면 투영 벡터 (y성분만 0으로)
   xz_plane_vector = np.array([
       current_elbow_x - shoulder_x,
       0,  # y성분 제거
       current_elbow_z - shoulder_z
   ])

   # 🎯 실제 벡터로 올림 각도 계산!
   elevation_angle_deg = vector_angle_deg(upper_arm_vector, xz_plane_vector)
   elbow_raise_ratio = min(elevation_angle_deg / 90.0, 1.0)

   print(f'elevation_angle_deg: {elevation_angle_deg:.2f}°, raise_ratio: {elbow_raise_ratio:.3f}')

   # 전방각 보정
   # adjusted_forward_angle = base_forward_angle * (1.0 - elbow_raise_ratio)
   # adjusted_forward_angle = max(adjusted_forward_angle, 0.0)

   # Option 1: 전방각을 음수까지 허용
   adjusted_forward_angle = base_forward_angle * (1.0 - elbow_raise_ratio * 2)

   # 최종 가이드라인 팔꿈치 위치 계산
   elbow_y = current_elbow_y  # 현재 높이 사용

   # 최소 각도 보정
   height_diff = elbow_y - shoulder_y
   min_angle_radians = math.radians(min_elbow_angle)
   min_height_diff = math.cos(min_angle_radians) * upper_arm_length

   if height_diff < min_height_diff:
       elbow_y = shoulder_y + min_height_diff
       height_diff = elbow_y - shoulder_y

   # 🎯 상완 길이와 올림 각도로 정확한 수평 거리 계산
   horizontal_projection = upper_arm_length * math.cos(math.radians(elevation_angle_deg))

   # 전방각 적용
   forward_angle_radians = math.radians(adjusted_forward_angle)
   x_offset = math.cos(forward_angle_radians) * horizontal_projection
   z_offset = math.sin(forward_angle_radians) * horizontal_projection

   # if side == "left":
   #     x_offset = -x_offset
   x_adjustment = 0.09  # 이 값을 조정해서 양쪽 팔 위치 제어
   z_adjustment = 0.001
   if side == "left":
       x_offset = -x_offset + x_adjustment  # 왼쪽: 음수로 만든 후 추가로 빼기
       z_offset = -z_offset + 0.001
   else:
       x_offset = x_offset - x_adjustment  # 오른쪽: 양수에 추가로 더하기

   # 최종 팔꿈치 좌표
   elbow_x = shoulder_x + x_offset
   elbow_z = shoulder_z + z_offset

   print(f'x_offset : {x_offset}, z_offset : {z_offset}')

   print(f'elbow_x : {elbow_x}, elbow_y : {elbow_y}, elbow_z : {elbow_z}')

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
    print(f'wrist: {wrist}')

    return wrist.tolist()