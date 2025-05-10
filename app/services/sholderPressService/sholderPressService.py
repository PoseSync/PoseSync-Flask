import numpy as np

from app.services.body_service.body_spec_service import get_body_info_for_dumbbell_shoulder_press
from app.util.math_util import normalize_vector
from app.util.pose_landmark_enum import PoseLandmark
from app.util.shoulderPress_util import calculate_elbow_position_by_forward_angle, \
    adjust_wrist_direction_to_preserve_min_angle

# AI 모델 가져오기
from app.ai.ai_model import fall_model

# 가속도 계산
from app.util.calculate_landmark_accerlation import calculate_acceleration


def process_dumbbell_shoulderPress(data):
    landmarks = data.get("landmarks", [])
    phone_number = data.get("phoneNumber")  # 개인식별자
    bone_lengths = data.get("bone_lengths", {})  # 첫 exercise_date 패킷 연결에서 계산한 뼈 길이

    # 현재 전달받은 landmark의 가속도 측정
    accerlation = calculate_acceleration(landmarks)

    if accerlation is not None:
        head_acc = accerlation['head_acceleration']
        pelvis_acc = accerlation['pelvis_acceleration']

        model_input = np.array(head_acc + pelvis_acc).reshape(1, 6)

        # 입력 데이터로 받은걸로 예측
        prediction = fall_model.predict(model_input)
        fall = bool(prediction[0] > 0.5)

        if fall:
            print("##########  낙상 감지 ##########")

    # ✅ 사용자 체형 + 신체 길이 조회
    body_info = get_body_info_for_dumbbell_shoulder_press(phone_number)
    arm_type = body_info["arm_type"]
    upper_arm_length = bone_lengths["left_upper_arm_length"]
    forearm_length = bone_lengths["left_forearm_length"]
    shoulder_width = bone_lengths["shoulder_width"]
    # db조회해서 뼈길이 가져오기
    # upper_arm_length = body_info["upper_arm_length"]
    # forearm_length = body_info["forearm_length"]
    # shoulder_width = body_info["shoulder_width"]

    # 어깨좌표 [0] : 왼쪽 [1] : 오른쪽
    shoulders_coord = [
        landmarks[PoseLandmark.LEFT_SHOULDER],
        landmarks[PoseLandmark.RIGHT_SHOULDER]
    ]
    # 팔꿈치 좌표
    elbows_coord = [
        landmarks[PoseLandmark.LEFT_ELBOW],
        landmarks[PoseLandmark.RIGHT_ELBOW]
    ]
    # 손목 좌표
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

        # 원래 visibility 값 저장
        elbow_visibility = landmarks[elbow_id].get('visibility', 1.0)

        landmarks[elbow_id]['x'] = elbow_pos[0]
        landmarks[elbow_id]['y'] = elbow_pos[1]
        landmarks[elbow_id]['z'] = elbow_pos[2]

        # visibility 값 복원
        landmarks[elbow_id]['visibility'] = elbow_visibility

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

        # 원래 visibility 값 저장
        wrist_visibility = landmarks[wrist_id].get('visibility', 1.0)

        landmarks[wrist_id]['x'] = wrist_pos[0]
        landmarks[wrist_id]['y'] = wrist_pos[1]
        landmarks[wrist_id]['z'] = wrist_pos[2]

        # visibility 값 복원
        landmarks[wrist_id]['visibility'] = wrist_visibility

    return data  # 수정된 data


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