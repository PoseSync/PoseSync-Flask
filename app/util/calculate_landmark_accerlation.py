import numpy as np
from collections import deque
import time
from app.util.pose_landmark_enum import PoseLandmark


# 위치 기록 버퍼
history = {
    'head': deque(maxlen=3),
    'pelvis': deque(maxlen=3)
}
timestamps = deque(maxlen=3)

def calculate_acceleration(landmarks):  # 인자명을 landmarks로 바꿈
    current_time = time.time()
    timestamps.append(current_time)

    head = landmarks[PoseLandmark.MOUTH_LEFT]
    pelvis = landmarks[PoseLandmark.LEFT_HIP]

    head_vec = np.array([head["x"], head["y"], head["z"]])
    pelvis_vec = np.array([pelvis["x"], pelvis["y"], pelvis["z"]])

    history['head'].append(head_vec)
    history['pelvis'].append(pelvis_vec)

    if len(history['head']) == 3 and len(timestamps) == 3:
        dt1 = timestamps[1] - timestamps[0]
        dt2 = timestamps[2] - timestamps[1]
        dt = (dt1 + dt2) / 2

        a_head = (history['head'][2] - 2 * history['head'][1] + history['head'][0]) / (dt ** 2)
        a_pelvis = (history['pelvis'][2] - 2 * history['pelvis'][1] + history['pelvis'][0]) / (dt ** 2)

        return {
            "head_acceleration": a_head.tolist(),
            "pelvis_acceleration": a_pelvis.tolist()
        }
    return None
