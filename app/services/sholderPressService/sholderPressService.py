import numpy as np

from app.util.pose_landmark_enum import PoseLandmark
from app.util.exercise_util.shoulderPress_util import calculate_elbow_position_by_forward_angle, \
    adjust_wrist_direction_to_preserve_min_angle
# 공유 전역 상태에서 body_type과 뼈길이 데이터 가져오기
from app.shared.global_state import press_counter


def process_dumbbell_shoulderPress(data):

    landmarks = data.get("landmarks", [])
    bone_lengths = data.get("bone_lengths", {})
    body_type = data.get("body_type", {})

    if not bone_lengths:
        raise Exception("사용자 뼈길이 정보가 없습니다.")

    # bone_lengths와 body_type 사용
    arm_type = body_type.get("arm_type", "AVG")



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
    # upper_arm_vecs = []
    # for side in [0, 1]:  # 0: left, 1: right
    #     vec = np.array([
    #         elbows_coord[side]['x'] - shoulders_coord[side]['x'],
    #         elbows_coord[side]['y'] - shoulders_coord[side]['y'],
    #         elbows_coord[side]['z'] - shoulders_coord[side]['z']
    #     ])
    #
    # # 전완 벡터 (elbow → wrist)
    # forearm_vecs = []
    # for side in [0, 1]:
    #     vec = np.array([
    #         wrists[side]['x'] - elbows_coord[side]['x'],
    #         wrists[side]['y'] - elbows_coord[side]['y'],
    #         wrists[side]['z'] - elbows_coord[side]['z']
    #     ])
    #
    # # 어깨 라인 벡터 (왼쪽 → 오른쪽)
    # shoulder_line_vec = normalize_vector(np.array([
    #     shoulders_coord[1]['x'] - shoulders_coord[0]['x'],
    #     shoulders_coord[1]['y'] - shoulders_coord[0]['y'],
    #     shoulders_coord[1]['z'] - shoulders_coord[0]['z']
    # ]))

    # ✅ 양쪽 팔 각각 처리
    for side in [0, 1]:
        side_label = "left" if side == 0 else "right"

        shoulder = shoulders_coord[side]
        elbow_y = elbows_coord[side]['y']  # 현재 팔꿈치 높이 유지

        # ✅ 전역변수에서 뼈길이 사용
        current_upper_arm_length = bone_lengths[f"{side_label}_upper_arm_length"]
        current_forearm_length = bone_lengths[f"{side_label}_forearm_length"]


        # print(f"{side_label} upper arm length: {current_upper_arm_length}")
        # print(f"{side_label} forearm length: {current_forearm_length}")


        # 🟥 팔꿈치 위치 계산 (전방 외각 유지)
        elbow_pos = calculate_elbow_position_by_forward_angle(
            shoulder_coord=[shoulder['x'], shoulder['y'], shoulder['z']],
            arm_type=arm_type,
            upper_arm_length=current_upper_arm_length,
            elbow_y=elbow_y,
            side=side_label  # side_label을 그대로 전달
        )

        # ⬇ landmarks에 elbow 좌표 업데이트
        if side_label == "left":
            elbow_id = PoseLandmark.LEFT_ELBOW
        else:  # side_label == "right"
            elbow_id = PoseLandmark.RIGHT_ELBOW

        # 원래 visibility 값 저장
        elbow_visibility = landmarks[elbow_id].get('visibility', 1.0)

        landmarks[elbow_id]['x'] = elbow_pos[0]
        landmarks[elbow_id]['y'] = elbow_pos[1]
        landmarks[elbow_id]['z'] = elbow_pos[2]

        # visibility 값 복원
        landmarks[elbow_id]['visibility'] = elbow_visibility

        # 2. 손목 위치 계산 (숄더프레스 기준 y+ 방향)
        wrist_pos = adjust_wrist_direction_to_preserve_min_angle(
            shoulder_coord=[
                shoulders_coord[side]['x'],
                shoulders_coord[side]['y'],
                shoulders_coord[side]['z']
            ],
            elbow_coord=elbow_pos,
            forearm_length=current_forearm_length,
            arm_type=arm_type,
            side=side_label  # side_label을 그대로 전달
        )

        # ⬇ landmarks에 wrist 좌표 업데이트
        if side_label == "left":
            wrist_id = PoseLandmark.LEFT_WRIST
        else:  # side_label == "right"
            wrist_id = PoseLandmark.RIGHT_WRIST

        # 원래 visibility 값 저장
        wrist_visibility = landmarks[wrist_id].get('visibility', 1.0)

        landmarks[wrist_id]['x'] = wrist_pos[0]
        landmarks[wrist_id]['y'] = wrist_pos[1]
        landmarks[wrist_id]['z'] = wrist_pos[2]

        # visibility 값 복원
        landmarks[wrist_id]['visibility'] = wrist_visibility

    # landmarks = landmark_stabilizer.stabilize_landmarks(landmarks, dead_zone=0.03)

    # 수정된 landmarks를 data에 다시 저장
    data["landmarks"] = landmarks


    # 운동 한 회가 완료되면 카운트 증가 --------------------------------------
    # press_counter가 None이 아닌 경우에만 카운팅 로직 실행
    if press_counter:
        # 왼팔 기준으로 운동 횟수 업데이트
        completed = press_counter.update(landmarks)

        # 운동 한 회가 완료되면 카운트 증가
        if completed:
            count = press_counter.count
            print(f"✅ 운동 횟수 변경: {count}회")
            data["count"] = count
        elif "count" not in data:
            # 이전 카운트 값이 없으면 현재 카운트 추가
            data["count"] = press_counter.count
        # 운동 한 회가 완료되면 카운트 증가 ------------------------------------


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