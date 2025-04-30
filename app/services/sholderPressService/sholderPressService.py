import numpy as np

from app.services.body_service.body_spec_service import get_body_info_for_dumbbell_shoulder_press
from app.util.math_util import normalize_vector
from app.util.pose_landmark_enum import PoseLandmark
from app.util.shoulderPress_util import calculate_elbow_position_by_forward_angle, adjust_wrist_direction_to_preserve_min_angle


def process_dumbbell_shoulderPress(data):

    landmarks = data.get("landmarks", [])
    phone_number = data.get("phoneNumber") # 개인식별자

    # ✅ 사용자 체형 + 신체 길이 조회
    body_info = get_body_info_for_dumbbell_shoulder_press(phone_number)
    arm_type = body_info["arm_type"]
    upper_arm_length = body_info["upper_arm_length"]
    forearm_length = body_info["forearm_length"]
    shoulder_width = body_info["shoulder_width"]

    #어깨좌표 [0] : 왼쪽 [1] : 오른쪽
    shoulders_coord = [
        landmarks[PoseLandmark.LEFT_SHOULDER],
        landmarks[PoseLandmark.RIGHT_SHOULDER]
    ]
    #팔꿈치 좌표
    elbows_coord = [
        landmarks[PoseLandmark.LEFT_ELBOW],
        landmarks[PoseLandmark.RIGHT_ELBOW]
    ]
    #손목 좌표
    wrists = [
        landmarks[PoseLandmark.LEFT_WRIST],
        landmarks[PoseLandmark.RIGHT_WRIST]
    ]

    # 상완 벡터 (shoulder → elbow)
    upper_arm_vecs = []
    for side in [0, 1]:  # 0: left, 1: right
        vec = np.array([
            elbows_coord[side]['x'] - shoulders_coord[side]['x'],
            elbows_coord[side]['y'] - shoulders_coord[side]['y'],
            elbows_coord[side]['z'] - shoulders_coord[side]['z']
        ])

    # 전완 벡터 (elbow → wrist)
    forearm_vecs = []
    for side in [0, 1]:
        vec = np.array([
            wrists[side]['x'] - elbows_coord[side]['x'],
            wrists[side]['y'] - elbows_coord[side]['y'],
            wrists[side]['z'] - elbows_coord[side]['z']
        ])

    # 어깨 라인 벡터 (왼쪽 → 오른쪽)
    shoulder_line_vec = normalize_vector(np.array([
        shoulders_coord[1]['x'] - shoulders_coord[0]['x'],
        shoulders_coord[1]['y'] - shoulders_coord[0]['y'],
        shoulders_coord[1]['z'] - shoulders_coord[0]['z']
    ]))

    # ✅ 양쪽 팔 각각 처리
    for side in [0, 1]:
        side_label = "left" if side == 0 else "right"

        shoulder = shoulders_coord[side]
        elbow_y = elbows_coord[side]['y']  # 현재 팔꿈치 높이 유지

        # 🟥 팔꿈치 위치 계산 (전방 외각 유지)
        elbow_pos = calculate_elbow_position_by_forward_angle(
            shoulder_coord=[shoulder['x'], shoulder['y'], shoulder['z']],
            arm_type=arm_type,
            upper_arm_length=upper_arm_length,
            elbow_y=elbow_y
        )

        # ⬇ landmarks에 elbow 좌표 업데이트
        elbow_id = PoseLandmark.LEFT_ELBOW if side == 0 else PoseLandmark.RIGHT_ELBOW
        landmarks[elbow_id]['x'] = elbow_pos[0]
        landmarks[elbow_id]['y'] = elbow_pos[1]
        landmarks[elbow_id]['z'] = elbow_pos[2]

        # 🟦 손목 위치 계산 (숄더프레스 기준 y+ 방향)
        wrist_pos = adjust_wrist_direction_to_preserve_min_angle(
            shoulder_coord=[
                shoulders_coord[side]['x'],
                shoulders_coord[side]['y'],
                shoulders_coord[side]['z']
            ],
            elbow_coord=elbow_pos,
            forearm_length=forearm_length,
            arm_type=arm_type
        )

        # ⬇ landmarks에 wrist 좌표 업데이트
        wrist_id = PoseLandmark.LEFT_WRIST if side == 0 else PoseLandmark.RIGHT_WRIST
        landmarks[wrist_id]['x'] = wrist_pos[0]
        landmarks[wrist_id]['y'] = wrist_pos[1]
        landmarks[wrist_id]['z'] = wrist_pos[2]

    return data #수정된 data


"""
{
  "phoneNumber": "01012345678",
  "exerciseType": "dumbbell_shoulder_press",
  "timestamp": "2025-04-15T13:28:56.928217",
  "landmarks": [
    { "x": 0.1, "y": 0.5, "z": 0.1 },  // LEFT_SHOULDER
    { "x": 0.3, "y": 0.5, "z": 0.1 },  // RIGHT_SHOULDER
    { "x": 0.1, "y": 0.3, "z": 0.1 },  // LEFT_ELBOW (updated)
    { "x": 0.3, "y": 0.3, "z": 0.1 },  // RIGHT_ELBOW (updated)
    { "x": 0.1, "y": 0.3, "z": 0.25 }, // LEFT_WRIST (updated, right-angle direction)
    { "x": 0.3, "y": 0.3, "z": 0.25 }  // RIGHT_WRIST (updated, right-angle direction)
  ]
}
"""