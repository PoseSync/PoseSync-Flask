import numpy as np

from app.util.pose_landmark_enum import PoseLandmark
from app.util.exercise_util.shoulderPress_util import calculate_elbow_position_by_forward_angle, \
    adjust_wrist_direction_to_preserve_min_angle
# 공유 전역 상태에서 body_type과 뼈길이 데이터 가져오기
import app.shared.global_state as global_state


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
            current_elbow_coord=[elbows_coord[side]['x'], elbows_coord[side]['y'], elbows_coord[side]['z']],
            arm_type=arm_type,
            upper_arm_length=current_upper_arm_length,
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

    if global_state.counter:
        # 왼팔 기준으로 운동 횟수 업데이트
        completed = global_state.counter.update(landmarks)

        # 운동 한 회가 완료되면 카운트 증가
        if completed:
            count = global_state.counter.count
            data["count"] = count
        elif "count" not in data:
            # 이전 카운트 값이 없으면 현재 카운트 추가
            data["count"] = global_state.counter.count
        # 운동 한 회가 완료되면 카운트 증가 ------------------------------------


    return data  # 수정된 data
