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

def calculate_acceleration(data):
    current_time = time.time()
    timestamps.append(current_time)

    # enum으로 인덱스 지정
    head = data["landmarks"][PoseLandmark.MOUTH_LEFT]
    pelvis = data["landmarks"][PoseLandmark.LEFT_HIP]

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
    return None  # 아직 계산 불가