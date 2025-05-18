import numpy as np

from app.shared.global_state import current_user_body_type
from app.util.pose_landmark_enum import PoseLandmark
from app.util.exercise_util.squat_util import (
    adjust_foot_width_only,
    calculate_knee_position_by_hip_height,
    clamp_hip_height,
    calculate_hip_center
)


def process_squat(data):
    """
    스쿼트 가이드라인 생성 서비스
    - 첫 프레임에서 기준점 고정 (stance_ref)
    - 발 너비만 조절하고 나란하게 정렬
    - 무릎은 엉덩이 높이에 연동하여 계산
    """
    landmarks = data.get("landmarks", [])
    bone_lengths = data.get("bone_lengths", {})

    # body_info에서 femur_type과 shoulder_width 가져오기
    # 실제로는 body_spec_service를 통해 가져와야 함
    phone_number = data.get("phoneNumber")

    # 임시로 기본값 설정 (실제로는 DB에서 가져와야 함)
    femur_type = current_user_body_type.get("femur_type", "AVG")
    shoulder_width = current_user_body_type.get("shoulder_width", 0.4)

    # 필요한 뼈 길이 정보
    femur_length = bone_lengths.get("left_thigh_length", 0.4)
    tibia_length = bone_lengths.get("left_calf_length", 0.35)

    # 현재 엉덩이 위치
    left_hip = landmarks[PoseLandmark.LEFT_HIP]
    right_hip = landmarks[PoseLandmark.RIGHT_HIP]

    # 엉덩이 중심 계산
    hip_center = calculate_hip_center(left_hip, right_hip)

    # 🔧 첫 프레임에서 기준값 고정
    if 'stance_ref' not in data:
        # 첫 호출: 좌표계 기준값 고정
        data['stance_ref'] = {
            'center_x': hip_center[0],  # 발 X 대칭 기준
            'ground_y': (landmarks[PoseLandmark.LEFT_ANKLE]['y'] + landmarks[PoseLandmark.RIGHT_ANKLE]['y']) / 2
        }
        print(f"✅ 스쿼트 기준점 고정: center_x={data['stance_ref']['center_x']}, ground_y={data['stance_ref']['ground_y']}")

    ref = data['stance_ref']
    center_x = ref['center_x']
    ground_y = ref['ground_y']

    # 엉덩이 높이 제한 적용 (지면 기준)
    constrained_hip_y = clamp_hip_height(hip_center[1], ground_y, femur_length, tibia_length)

    # 제한된 높이로 엉덩이 위치 업데이트
    if constrained_hip_y != hip_center[1]:
        hip_diff = constrained_hip_y - hip_center[1]
        landmarks[PoseLandmark.LEFT_HIP]['y'] = left_hip['y'] + hip_diff
        landmarks[PoseLandmark.RIGHT_HIP]['y'] = right_hip['y'] + hip_diff

        # 업데이트된 엉덩이 중심 재계산
        hip_center[1] = constrained_hip_y

    # --- 발 X만 조절 ---
    left_ankle_pos, right_ankle_pos = adjust_foot_width_only(
        hip_center=[center_x, hip_center[1], hip_center[2]],  # x 고정
        shoulder_width=shoulder_width,
        femur_type=femur_type,
        current_left_ankle=landmarks[PoseLandmark.LEFT_ANKLE],
        current_right_ankle=landmarks[PoseLandmark.RIGHT_ANKLE]
    )

    # y 고정 (지면 기준)
    left_ankle_pos[1] = ground_y
    right_ankle_pos[1] = ground_y

    # 발목 위치 업데이트
    left_ankle_visibility = landmarks[PoseLandmark.LEFT_ANKLE].get('visibility', 1.0)
    right_ankle_visibility = landmarks[PoseLandmark.RIGHT_ANKLE].get('visibility', 1.0)

    landmarks[PoseLandmark.LEFT_ANKLE]['x'] = left_ankle_pos[0]
    landmarks[PoseLandmark.LEFT_ANKLE]['y'] = left_ankle_pos[1]
    landmarks[PoseLandmark.LEFT_ANKLE]['z'] = left_ankle_pos[2]
    landmarks[PoseLandmark.LEFT_ANKLE]['visibility'] = left_ankle_visibility

    landmarks[PoseLandmark.RIGHT_ANKLE]['x'] = right_ankle_pos[0]
    landmarks[PoseLandmark.RIGHT_ANKLE]['y'] = right_ankle_pos[1]
    landmarks[PoseLandmark.RIGHT_ANKLE]['z'] = right_ankle_pos[2]
    landmarks[PoseLandmark.RIGHT_ANKLE]['visibility'] = right_ankle_visibility

    # 무릎 위치 계산 (엉덩이 높이에 연동)
    left_knee_pos = calculate_knee_position_by_hip_height(
        hip_coord=[landmarks[PoseLandmark.LEFT_HIP]['x'],
                   landmarks[PoseLandmark.LEFT_HIP]['y'],
                   landmarks[PoseLandmark.LEFT_HIP]['z']],
        ankle_coord=left_ankle_pos,
        femur_length=femur_length,
        tibia_length=tibia_length,
        femur_type=femur_type,
        side="left"
    )

    right_knee_pos = calculate_knee_position_by_hip_height(
        hip_coord=[landmarks[PoseLandmark.RIGHT_HIP]['x'],
                   landmarks[PoseLandmark.RIGHT_HIP]['y'],
                   landmarks[PoseLandmark.RIGHT_HIP]['z']],
        ankle_coord=right_ankle_pos,
        femur_length=femur_length,
        tibia_length=tibia_length,
        femur_type=femur_type,
        side="right"
    )

    # 무릎 위치 업데이트
    left_knee_visibility = landmarks[PoseLandmark.LEFT_KNEE].get('visibility', 1.0)
    right_knee_visibility = landmarks[PoseLandmark.RIGHT_KNEE].get('visibility', 1.0)

    landmarks[PoseLandmark.LEFT_KNEE]['x'] = left_knee_pos[0]
    landmarks[PoseLandmark.LEFT_KNEE]['y'] = left_knee_pos[1]
    landmarks[PoseLandmark.LEFT_KNEE]['z'] = left_knee_pos[2]
    landmarks[PoseLandmark.LEFT_KNEE]['visibility'] = left_knee_visibility

    landmarks[PoseLandmark.RIGHT_KNEE]['x'] = right_knee_pos[0]
    landmarks[PoseLandmark.RIGHT_KNEE]['y'] = right_knee_pos[1]
    landmarks[PoseLandmark.RIGHT_KNEE]['z'] = right_knee_pos[2]
    landmarks[PoseLandmark.RIGHT_KNEE]['visibility'] = right_knee_visibility

    # 업데이트된 landmarks를 data에 저장
    data["landmarks"] = landmarks


    landmarks[PoseLandmark.LEFT_ANKLE]['z'] = left_ankle_pos[2]

    landmarks[PoseLandmark.LEFT_ANKLE]['visibility'] = left_ankle_visibility

    landmarks[PoseLandmark.RIGHT_ANKLE]['x'] = right_ankle_pos[0]
    landmarks[PoseLandmark.RIGHT_ANKLE]['y'] = right_ankle_pos[1]
    landmarks[PoseLandmark.RIGHT_ANKLE]['z'] = right_ankle_pos[2]
    landmarks[PoseLandmark.RIGHT_ANKLE]['visibility'] = right_ankle_visibility

    # 무릎 위치 계산 (엉덩이 높이에 연동)
    left_knee_pos = calculate_knee_position_by_hip_height(
        hip_coord=[landmarks[PoseLandmark.LEFT_HIP]['x'],
                   landmarks[PoseLandmark.LEFT_HIP]['y'],
                   landmarks[PoseLandmark.LEFT_HIP]['z']],
        ankle_coord=left_ankle_pos,
        femur_length=femur_length,
        tibia_length=tibia_length,
        femur_type=femur_type,
        side="left"
    )

    right_knee_pos = calculate_knee_position_by_hip_height(
        hip_coord=[landmarks[PoseLandmark.RIGHT_HIP]['x'],
                   landmarks[PoseLandmark.RIGHT_HIP]['y'],
                   landmarks[PoseLandmark.RIGHT_HIP]['z']],
        ankle_coord=right_ankle_pos,
        femur_length=femur_length,
        tibia_length=tibia_length,
        femur_type=femur_type,
        side="right"
    )

    # 무릎 위치 업데이트
    left_knee_visibility = landmarks[PoseLandmark.LEFT_KNEE].get('visibility', 1.0)
    right_knee_visibility = landmarks[PoseLandmark.RIGHT_KNEE].get('visibility', 1.0)

    landmarks[PoseLandmark.LEFT_KNEE]['x'] = left_knee_pos[0]
    landmarks[PoseLandmark.LEFT_KNEE]['y'] = left_knee_pos[1]
    landmarks[PoseLandmark.LEFT_KNEE]['z'] = left_knee_pos[2]
    landmarks[PoseLandmark.LEFT_KNEE]['visibility'] = left_knee_visibility

    landmarks[PoseLandmark.RIGHT_KNEE]['x'] = right_knee_pos[0]
    landmarks[PoseLandmark.RIGHT_KNEE]['y'] = right_knee_pos[1]
    landmarks[PoseLandmark.RIGHT_KNEE]['z'] = right_knee_pos[2]
    landmarks[PoseLandmark.RIGHT_KNEE]['visibility'] = right_knee_visibility

    # 업데이트된 landmarks를 data에 저장
    data["landmarks"] = landmarks

    return data