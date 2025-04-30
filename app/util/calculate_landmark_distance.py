import math
from app.util.pose_landmark_enum import PoseLandmark  # PoseLandmark Enum 불러오기

# 1. 이름 기반 connections
connections = {
    "NOSE": ["LEFT_EYE_INNER", "RIGHT_EYE_INNER"],
    "LEFT_EYE_INNER": ["NOSE", "LEFT_EYE"],
    "LEFT_EYE": ["LEFT_EYE_INNER", "LEFT_EYE_OUTER"],
    "LEFT_EYE_OUTER": ["LEFT_EYE", "LEFT_EAR"],
    "RIGHT_EYE_INNER": ["NOSE", "RIGHT_EYE"],
    "RIGHT_EYE": ["RIGHT_EYE_INNER", "RIGHT_EYE_OUTER"],
    "RIGHT_EYE_OUTER": ["RIGHT_EYE", "RIGHT_EAR"],
    "LEFT_EAR": ["LEFT_EYE_OUTER"],
    "RIGHT_EAR": ["RIGHT_EYE_OUTER"],

    "MOUTH_LEFT": ["MOUTH_RIGHT"],
    "MOUTH_RIGHT": ["MOUTH_LEFT"],

    "LEFT_SHOULDER": ["RIGHT_SHOULDER", "LEFT_ELBOW"],
    "RIGHT_SHOULDER": ["LEFT_SHOULDER", "RIGHT_ELBOW"],

    "LEFT_ELBOW": ["LEFT_SHOULDER", "LEFT_WRIST"],
    "RIGHT_ELBOW": ["RIGHT_SHOULDER", "RIGHT_WRIST"],

    "LEFT_WRIST": ["LEFT_ELBOW", "LEFT_PINKY", "LEFT_INDEX", "LEFT_THUMB"],
    "RIGHT_WRIST": ["RIGHT_ELBOW", "RIGHT_PINKY", "RIGHT_INDEX", "RIGHT_THUMB"],

    "LEFT_PINKY": ["LEFT_WRIST"],
    "RIGHT_PINKY": ["RIGHT_WRIST"],

    "LEFT_INDEX": ["LEFT_WRIST"],
    "RIGHT_INDEX": ["RIGHT_WRIST"],

    "LEFT_THUMB": ["LEFT_WRIST"],
    "RIGHT_THUMB": ["RIGHT_WRIST"],

    "LEFT_HIP": ["RIGHT_HIP", "LEFT_KNEE"],
    "RIGHT_HIP": ["LEFT_HIP", "RIGHT_KNEE"],

    "LEFT_KNEE": ["LEFT_HIP", "LEFT_ANKLE"],
    "RIGHT_KNEE": ["RIGHT_HIP", "RIGHT_ANKLE"],

    "LEFT_ANKLE": ["LEFT_KNEE", "LEFT_HEEL", "LEFT_FOOT_INDEX"],
    "RIGHT_ANKLE": ["RIGHT_KNEE", "RIGHT_HEEL", "RIGHT_FOOT_INDEX"],

    "LEFT_HEEL": ["LEFT_ANKLE"],
    "RIGHT_HEEL": ["RIGHT_ANKLE"],

    "LEFT_FOOT_INDEX": ["LEFT_ANKLE"],
    "RIGHT_FOOT_INDEX": ["RIGHT_ANKLE"]
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


# TODO 'LANDMARK1-LANDMARK2' key로 구성된 distances를  간결한 key로 바꿔서 반환
def map_distances_to_named_keys(distances, name_map):

    mapped = {}
    for key, value in distances.items():
        readable_key = name_map.get(key)
        if readable_key:
            mapped[readable_key] = value
    return mapped
