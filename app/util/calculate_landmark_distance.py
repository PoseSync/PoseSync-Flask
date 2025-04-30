import math
from app.util.pose_landmark_enum import PoseLandmark  # PoseLandmark Enum 불러오기

# 1. 이름 기반 connections
connections = {
    # 팔 길이 + 어깨 너비
    "LEFT_SHOULDER": ["LEFT_ELBOW", "RIGHT_SHOULDER"],  # 상완 | 어깨 너비
    "LEFT_ELBOW": ["LEFT_WRIST"],                       # 왼쪽 전완

    "RIGHT_SHOULDER": ["RIGHT_ELBOW"],                  # 오른쪽 상완
    "RIGHT_ELBOW": ["RIGHT_WRIST"],                     # 오른쪽 전완

    # 다리 길이 + 고관절 너비
    "LEFT_HIP": ["LEFT_KNEE", "RIGHT_HIP"],             # 대퇴골길이 | 고관절 너비
    "LEFT_KNEE": ["LEFT_ANKLE"],                        # 정강이 길이

    "RIGHT_HIP": ["RIGHT_KNEE"],                        # 오른쪽 대퇴골길이
    "RIGHT_KNEE": ["RIGHT_ANKLE"]                       # 오른쪽 정강이 길이
}


# key: "LANDMARK1-LANDMARK2" → value: 간결한 영어 식별자
bone_name_map = {
    "LEFT_SHOULDER-RIGHT_SHOULDER": "shoulder_width",
    "LEFT_HIP-RIGHT_HIP": "hip_width",

    "LEFT_SHOULDER-LEFT_ELBOW": "left_upper_arm_length",
    "LEFT_ELBOW-LEFT_WRIST": "left_forearm_length",

    "RIGHT_SHOULDER-RIGHT_ELBOW": "right_upper_arm_length",
    "RIGHT_ELBOW-RIGHT_WRIST": "right_forearm_length",

    "LEFT_HIP-LEFT_KNEE": "left_thigh_length",
    "LEFT_KNEE-LEFT_ANKLE": "left_calf_length",

    "RIGHT_HIP-RIGHT_KNEE": "right_thigh_length",
    "RIGHT_KNEE-RIGHT_ANKLE": "right_calf_length"
}



# 2. 거리 계산 함수
def calculate_distance(p1, p2):
    return math.sqrt(
        (p1['x'] - p2['x'])**2 +
        (p1['y'] - p2['y'])**2 +
        (p1['z'] - p2['z'])**2
    )

# 3. 이름 기반으로 연결된 landmarks 거리 계산
def calculate_named_linked_distances(landmarks, connections):
    distances = {}

    # id → landmark dict 매핑
    id_to_landmark = {lm['id']: lm for lm in landmarks}
    id_to_name = {lm['id']: lm['name'] for lm in landmarks}
    name_to_id = {v: k for k, v in id_to_name.items()}  # 이름 → id 매핑

    for start_name, linked_names in connections.items():
        for end_name in linked_names:
            start_id = name_to_id.get(start_name)
            end_id = name_to_id.get(end_name)
            if start_id is None or end_id is None:
                continue  # 데이터 누락 예외처리

            p1 = id_to_landmark[start_id]
            p2 = id_to_landmark[end_id]

            distance = calculate_distance(p1, p2)
            key = f"{start_name}-{end_name}"
            distances[key] = distance

    return distances


# 'LANDMARK1-LANDMARK2' key로 구성된 distances를  간결한 key로 바꿔서 반환
def map_distances_to_named_keys(distances, name_map):

    mapped = {}
    for key, value in distances.items():
        readable_key = name_map.get(key)
        if readable_key:
            mapped[readable_key] = value
    return mapped
