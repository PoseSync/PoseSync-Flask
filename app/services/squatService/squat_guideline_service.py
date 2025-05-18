from app.util.pose_landmark_enum import PoseLandmark
from app.util.exercise_util.squat_guide_util import (
    adjust_foot_width_only,
    calculate_knee_position_by_hip_height,
    clamp_hip_height,
    calculate_hip_center
)

def process_squat_guideline(data):
    """
    스쿼트 가이드라인 생성 서비스
    - 발 너비만 조절하고 나란하게 정렬
    - 무릎은 엉덩이 높이에 연동하여 계산
    """
    landmarks = data.get("landmarks", [])
    bone_lengths = data.get("bone_lengths", {})
    
    # body_info에서 femur_type과 shoulder_width 가져오기
    # 실제로는 body_spec_service를 통해 가져와야 함
    phone_number = data.get("phoneNumber")
    
    # 임시로 기본값 설정 (실제로는 DB에서 가져와야 함)
    femur_type = "AVG"  # 실제로는 get_body_info_for_squat_guideline()에서 가져오기
    shoulder_width = bone_lengths.get("shoulder_width", 0.4)  # 기본값
    
    # 필요한 뼈 길이 정보
    femur_length = bone_lengths.get("left_thigh_length", 0.4)
    tibia_length = bone_lengths.get("left_calf_length", 0.35)
    
    # 현재 엉덩이 위치
    left_hip = landmarks[PoseLandmark.LEFT_HIP]
    right_hip = landmarks[PoseLandmark.RIGHT_HIP]
    
    # 엉덩이 중심 계산
    hip_center = calculate_hip_center(left_hip, right_hip)
    
    # 엉덩이 높이 제한 적용
    constrained_hip_y = clamp_hip_height(hip_center[1], femur_length, tibia_length, femur_type)
    
    # 제한된 높이로 엉덩이 위치 업데이트
    if constrained_hip_y != hip_center[1]:
        hip_diff = constrained_hip_y - hip_center[1]
        landmarks[PoseLandmark.LEFT_HIP]['y'] = left_hip['y'] + hip_diff
        landmarks[PoseLandmark.RIGHT_HIP]['y'] = right_hip['y'] + hip_diff
        
        # 업데이트된 엉덩이 중심 재계산
        hip_center[1] = constrained_hip_y
    
    # 발 너비만 조절 (Y, Z는 사용자 위치 기반 유지)
    left_ankle_pos, right_ankle_pos = adjust_foot_width_only(
        hip_center, 
        shoulder_width, 
        femur_type,
        landmarks[PoseLandmark.LEFT_ANKLE],
        landmarks[PoseLandmark.RIGHT_ANKLE]
    )
    
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
    
    return data
