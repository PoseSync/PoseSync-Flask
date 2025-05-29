import numpy as np

from app.util.pose_landmark_enum import PoseLandmark
from app.util.exercise_util.side_lateral_raise_util import (
    calculate_elbow_position_for_lateral_raise,
    calculate_wrist_position_for_lateral_raise
)
# 공유 전역 상태에서 body_type과 뼈길이 데이터 가져오기
import app.shared.global_state as global_state


def process_side_lateral_raise(data):
    """
    사이드 레터럴 레이즈 가이드라인 생성 서비스
    - 양쪽 팔을 개별적으로 처리
    - 각 팔의 사용자 현재 위치를 고려하여 가이드라인 생성
    """
    landmarks = data.get("landmarks", [])
    bone_lengths = data.get("bone_lengths", {})
    body_type = data.get("body_type", {})

    if not bone_lengths:
        raise Exception("사용자 뼈길이 정보가 없습니다.")

    # 체형 정보
    arm_type = body_type.get("arm_type", "AVG")

    # 필요한 랜드마크 추출
    shoulders_coord = [
        landmarks[PoseLandmark.LEFT_SHOULDER],
        landmarks[PoseLandmark.RIGHT_SHOULDER]
    ]
    elbows_coord = [
        landmarks[PoseLandmark.LEFT_ELBOW],
        landmarks[PoseLandmark.RIGHT_ELBOW]
    ]
    wrists_coord = [
        landmarks[PoseLandmark.LEFT_WRIST],
        landmarks[PoseLandmark.RIGHT_WRIST]
    ]

    # ✅ 양쪽 팔 각각 처리
    for side in [0, 1]:
        side_label = "left" if side == 0 else "right"

        shoulder = shoulders_coord[side]
        current_elbow = elbows_coord[side]
        current_wrist = wrists_coord[side]

        # ✅ 전역변수에서 뼈길이 사용
        current_upper_arm_length = bone_lengths[f"{side_label}_upper_arm_length"]
        current_forearm_length = bone_lengths[f"{side_label}_forearm_length"]

        print(f"{side_label} upper arm length: {current_upper_arm_length}")
        print(f"{side_label} forearm length: {current_forearm_length}")

        # 🟥 팔꿈치 위치 계산 (레터럴 레이즈 특화)
        elbow_pos = calculate_elbow_position_for_lateral_raise(
            shoulder_coord=[shoulder['x'], shoulder['y'], shoulder['z']],
            current_elbow_coord=[current_elbow['x'], current_elbow['y'], current_elbow['z']],
            arm_type=arm_type,
            upper_arm_length=current_upper_arm_length,
            side=side_label
        )

        # 🟥 손목 위치 계산 (레터럴 레이즈 특화)
        wrist_pos = calculate_wrist_position_for_lateral_raise(
            shoulder_coord=[shoulder['x'], shoulder['y'], shoulder['z']],
            elbow_coord=elbow_pos,
            current_wrist_coord=[current_wrist['x'], current_wrist['y'], current_wrist['z']],
            forearm_length=current_forearm_length,
            arm_type=arm_type,
            side=side_label
        )

        # ⬇ landmarks에 elbow 좌표 업데이트
        if side_label == "left":
            elbow_id = PoseLandmark.LEFT_ELBOW
            wrist_id = PoseLandmark.LEFT_WRIST
        else:  # side_label == "right"
            elbow_id = PoseLandmark.RIGHT_ELBOW
            wrist_id = PoseLandmark.RIGHT_WRIST

        # 원래 visibility 값 저장
        elbow_visibility = landmarks[elbow_id].get('visibility', 1.0)
        wrist_visibility = landmarks[wrist_id].get('visibility', 1.0)

        # 팔꿈치 좌표 업데이트
        landmarks[elbow_id]['x'] = elbow_pos[0]
        landmarks[elbow_id]['y'] = elbow_pos[1]
        landmarks[elbow_id]['z'] = elbow_pos[2]
        landmarks[elbow_id]['visibility'] = elbow_visibility

        # 손목 좌표 업데이트
        landmarks[wrist_id]['x'] = wrist_pos[0]
        landmarks[wrist_id]['y'] = wrist_pos[1]
        landmarks[wrist_id]['z'] = wrist_pos[2]
        landmarks[wrist_id]['visibility'] = wrist_visibility

    # 수정된 landmarks를 data에 다시 저장
    data["landmarks"] = landmarks

    # 운동 한 회가 완료되면 카운트 증가 --------------------------------------
    print(f'❌ 카운터 시작 {global_state.counter}')

    if global_state.counter:
        # 왼팔 기준으로 운동 횟수 업데이트
        completed = global_state.counter.update(landmarks)

        # 운동 한 회가 완료되면 카운트 증가
        if completed:
            count = global_state.counter.count
            print(f"✅ 사이드 레터럴 레이즈 횟수: {count}회")
            data["count"] = count
        elif "count" not in data:
            # 이전 카운트 값이 없으면 현재 카운트 추가
            data["count"] = global_state.counter.count

    return data  # 수정된 data