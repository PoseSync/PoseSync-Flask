import numpy as np
from app.util.pose_landmark_enum import PoseLandmark
from app.util.exercise_util.barbell_curl_util import (
    calculate_elbow_position_for_barbell_curl,
    calculate_wrist_position_for_barbell_curl,
    create_symmetric_arm_positions
)
import app.shared.global_state as global_state



def process_barbell_curl(data):
    """
    바벨컬 가이드라인 생성 서비스
    - 오른팔을 기준으로 계산 후 왼팔 대칭 적용
    - 팔꿈치 → 손목 순서로 위치 계산
    """
    landmarks = data.get("landmarks", [])
    bone_lengths = data.get("bone_lengths", {})
    body_type = data.get("body_type", {})

    if not bone_lengths:
        raise Exception("사용자 뼈길이 정보가 없습니다.")

    # 체형 정보
    arm_type = body_type.get("arm_type", "AVG")

    # 필요한 랜드마크 추출
    left_shoulder = landmarks[PoseLandmark.LEFT_SHOULDER]
    right_shoulder = landmarks[PoseLandmark.RIGHT_SHOULDER]
    left_hip = landmarks[PoseLandmark.LEFT_HIP]
    right_hip = landmarks[PoseLandmark.RIGHT_HIP]
    left_elbow = landmarks[PoseLandmark.LEFT_ELBOW]
    right_elbow = landmarks[PoseLandmark.RIGHT_ELBOW]
    left_wrist = landmarks[PoseLandmark.LEFT_WRIST]
    right_wrist = landmarks[PoseLandmark.RIGHT_WRIST]

    # 몸 중심선 계산
    body_center_x = (left_shoulder['x'] + right_shoulder['x']) / 2

    # 어깨 너비 계산
    shoulder_width = bone_lengths.get("shoulder_width", 0.4)

    # 오른팔 뼈 길이
    right_upper_arm_length = bone_lengths.get("right_upper_arm_length", 0.3)
    right_forearm_length = bone_lengths.get("right_forearm_length", 0.25)

    # 1. 오른팔 팔꿈치 위치 계산
    right_elbow_pos = calculate_elbow_position_for_barbell_curl(
        shoulder_coord=[right_shoulder['x'], right_shoulder['y'], right_shoulder['z']],
        hip_coord=[right_hip['x'], right_hip['y'], right_hip['z']],
        current_elbow_coord=[right_elbow['x'], right_elbow['y'], right_elbow['z']],
        arm_type=arm_type,
        upper_arm_length=right_upper_arm_length,
        side="right"
    )

    # 2. 오른팔 손목 위치 계산
    right_wrist_pos = calculate_wrist_position_for_barbell_curl(
        elbow_coord=right_elbow_pos,
        current_wrist_coord=[right_wrist['x'], right_wrist['y'], right_wrist['z']],
        shoulder_width=shoulder_width,
        forearm_length=right_forearm_length,
        arm_type=arm_type,
        side="right"
    )

    # 3. 왼팔 대칭 위치 생성
    left_elbow_pos, left_wrist_pos = create_symmetric_arm_positions(
        right_elbow_pos=right_elbow_pos,
        right_wrist_pos=right_wrist_pos,
        body_center_x=body_center_x
    )

    # 4. 랜드마크 업데이트
    # 오른팔 팔꿈치
    right_elbow_visibility = landmarks[PoseLandmark.RIGHT_ELBOW].get('visibility', 1.0)
    landmarks[PoseLandmark.RIGHT_ELBOW]['x'] = right_elbow_pos[0]
    landmarks[PoseLandmark.RIGHT_ELBOW]['y'] = right_elbow_pos[1]
    landmarks[PoseLandmark.RIGHT_ELBOW]['z'] = right_elbow_pos[2]
    landmarks[PoseLandmark.RIGHT_ELBOW]['visibility'] = right_elbow_visibility

    # 오른팔 손목
    right_wrist_visibility = landmarks[PoseLandmark.RIGHT_WRIST].get('visibility', 1.0)
    landmarks[PoseLandmark.RIGHT_WRIST]['x'] = right_wrist_pos[0]
    landmarks[PoseLandmark.RIGHT_WRIST]['y'] = right_wrist_pos[1]
    landmarks[PoseLandmark.RIGHT_WRIST]['z'] = right_wrist_pos[2]
    landmarks[PoseLandmark.RIGHT_WRIST]['visibility'] = right_wrist_visibility

    # 왼팔 팔꿈치
    left_elbow_visibility = landmarks[PoseLandmark.LEFT_ELBOW].get('visibility', 1.0)
    landmarks[PoseLandmark.LEFT_ELBOW]['x'] = left_elbow_pos[0]
    landmarks[PoseLandmark.LEFT_ELBOW]['y'] = left_elbow_pos[1]
    landmarks[PoseLandmark.LEFT_ELBOW]['z'] = left_elbow_pos[2]
    landmarks[PoseLandmark.LEFT_ELBOW]['visibility'] = left_elbow_visibility

    # 왼팔 손목
    left_wrist_visibility = landmarks[PoseLandmark.LEFT_WRIST].get('visibility', 1.0)
    landmarks[PoseLandmark.LEFT_WRIST]['x'] = left_wrist_pos[0]
    landmarks[PoseLandmark.LEFT_WRIST]['y'] = left_wrist_pos[1]
    landmarks[PoseLandmark.LEFT_WRIST]['z'] = left_wrist_pos[2]
    landmarks[PoseLandmark.LEFT_WRIST]['visibility'] = left_wrist_visibility

    # 5. 운동 횟수 카운팅 (counter가 있는 경우)
    if global_state.counter:
        # 오른팔 기준으로 카운팅
        completed = global_state.counter.update(landmarks)

        if completed:
            count = global_state. counter.count
            print(f"✅ 바벨컬 횟수: {count}회")
            data["count"] = count
        elif "count" not in data:
            data["count"] = global_state.counter.count

    # 수정된 landmarks를 data에 저장
    data["landmarks"] = landmarks

    return data