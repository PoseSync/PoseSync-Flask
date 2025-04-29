import math
from app.util.pose_landmark_enum import PoseLandmark  # PoseLandmark Enum 불러오기

# 1. 이름 기반 connections
connections = {
    "NOSE": ["LEFT_EYE_INNER", "RIGHT_EYE_INNER"],
    "LEFT_EYE_INNER": ["NOSE", "LEFT_EYE"],
    "LEFT_EYE": ["LEFT_EYE_INNER", "LEFT_EYE_OUTER"],
    "LEFT_EYE_OUTER": ["LEFT_EYE"],
    "RIGHT_EYE_INNER": ["NOSE", "RIGHT_EYE"],
    "RIGHT_EYE": ["RIGHT_EYE_INNER", "RIGHT_EYE_OUTER"],
    "RIGHT_EYE_OUTER": ["RIGHT_EYE", "RIGHT_EAR"],
    "LEFT_EAR": ["RIGHT_EAR"],
    "RIGHT_EAR": ["RIGHT_EYE_OUTER", "LEFT_EAR"],
    "MOUTH_LEFT": ["MOUTH_RIGHT"],
    "MOUTH_RIGHT": ["MOUTH_LEFT"],
    "LEFT_SHOULDER": ["RIGHT_SHOULDER", "LEFT_ELBOW"],
    "RIGHT_SHOULDER": ["LEFT_SHOULDER", "RIGHT_ELBOW"],
    "LEFT_ELBOW": ["LEFT_SHOULDER", "LEFT_WRIST"],
    "RIGHT_ELBOW": ["RIGHT_SHOULDER", "RIGHT_WRIST"],
    "LEFT_WRIST": ["LEFT_ELBOW", "LEFT_PINKY"],
    "RIGHT_WRIST": ["RIGHT_ELBOW", "RIGHT_PINKY"],
    "LEFT_PINKY": ["LEFT_WRIST", "LEFT_INDEX"],
    "RIGHT_PINKY": ["RIGHT_WRIST", "RIGHT_INDEX"],
    "LEFT_INDEX": ["LEFT_PINKY", "LEFT_THUMB"],
    "RIGHT_INDEX": ["RIGHT_PINKY", "RIGHT_THUMB"],
    "LEFT_THUMB": ["LEFT_INDEX", "RIGHT_THUMB"],
    "RIGHT_THUMB": ["RIGHT_INDEX", "LEFT_THUMB"],
    "LEFT_HIP": ["RIGHT_HIP"],
    "RIGHT_HIP": ["LEFT_HIP", "RIGHT_KNEE"],
    "LEFT_KNEE": ["RIGHT_KNEE"],
    "RIGHT_KNEE": ["RIGHT_HIP", "LEFT_KNEE", "RIGHT_ANKLE"],
    "LEFT_ANKLE": ["RIGHT_ANKLE"],
    "RIGHT_ANKLE": ["RIGHT_KNEE", "LEFT_ANKLE", "RIGHT_HEEL", "RIGHT_FOOT_INDEX"],
    "LEFT_HEEL": ["RIGHT_HEEL", "LEFT_FOOT_INDEX"],
    "RIGHT_HEEL": ["RIGHT_ANKLE", "LEFT_HEEL"],
    "LEFT_FOOT_INDEX": ["LEFT_HEEL"],
    "RIGHT_FOOT_INDEX": ["RIGHT_ANKLE"]
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
