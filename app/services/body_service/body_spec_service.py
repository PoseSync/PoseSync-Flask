"""
사용자 전화번호로 필요한 body_type과 body_data를 한 번에 조회하여 딕셔너리로 반환
"""
from app.models import User, BodyData, BodyType


# 숄더프레스
def get_body_info_for_dumbbell_shoulder_press(phone_number):
    user = User.query.filter_by(phone_number=phone_number).first()
    if not user:
        raise Exception("❌ 사용자 없음")

    # 필요한 필드만 조회
    body_type = BodyType.query \
        .with_entities(BodyType.arm_type, BodyType.shoulder_type) \
        .filter_by(user_id=user.user_id) \
        .first()

    body_data = BodyData.query \
        .with_entities(
            BodyData.upper_arm_length,
            BodyData.forearm_length,
            BodyData.shoulder_width
        ) \
        .filter_by(user_id=user.user_id) \
        .first()

    if not body_type or not body_data:
        raise Exception("❌ 체형 또는 신체 데이터 없음")

    return {
        "arm_type": body_type.arm_type,   # 상완 길이 타입
        "shoulder_type": body_type.shoulder_type, # 어깨 너비 타입
        "upper_arm_length": float(body_data.upper_arm_length), # 상완 길이
        "forearm_length": float(body_data.forearm_length), # 전완 길이
        "shoulder_width": float(body_data.shoulder_width) # 어깨 너비
    }



# 스쿼트(임시)
# app/services/body_service.py
def get_body_info_for_squat(phone_number):
    """
    스쿼트 수행을 위한 최소한의 체형/신체 정보 조회
    """
    user = User.query.filter_by(phone_number=phone_number).first()
    if not user:
        raise Exception("❌ 사용자 없음")

    # 필요한 체형만 조회 (ex. 대퇴골 길이에 따른 분석)
    body_type = BodyType.query \
        .with_entities(BodyType.femur_type, BodyType.hip_wide_type) \
        .filter_by(user_id=user.user_id) \
        .first()

    # 필요한 신체길이만 조회
    body_data = BodyData.query \
        .with_entities(
            BodyData.femur_length,
            BodyData.hip_joint_width
        ) \
        .filter_by(user_id=user.user_id) \
        .first()

    if not body_type or not body_data:
        raise Exception("❌ 체형 또는 신체 데이터 없음")

    return {
        "femur_type": body_type.femur_type,
        "hip_wide_type": body_type.hip_wide_type,
        "femur_length": float(body_data.femur_length),
        "hip_joint_width": float(body_data.hip_joint_width)
    }

def get_all_body_info(phone_number):
    """사용자의 모든 체형/신체 정보를 한 번에 조회"""
    user = User.query.filter_by(phone_number=phone_number).first()
    if not user:
        raise Exception("❌ 사용자 없음")

    body_type = BodyType.query.filter_by(user_id=user.user_id).first()
    # body_data = BodyData.query.filter_by(user_id=user.user_id).first()
    print(f'{phone_number=} 사용자의 체형정보 가져옴')

    if not body_type:
        raise Exception("❌ 체형 또는 신체 데이터 없음")

    return {
        # body_type 전체
        "arm_type": body_type.arm_type,
        "femur_type": body_type.femur_type,
        "shoulder_type": body_type.shoulder_type,
        "hip_wide_type": body_type.hip_wide_type,
        "upper_lower_body_type": body_type.upper_lower_body_type,
        
        # body_data 전체  
        # "upper_arm_length": float(body_data.upper_arm_length),
        # "forearm_length": float(body_data.forearm_length),
        # "femur_length": float(body_data.femur_length),
        # "tibia_length": float(body_data.tibia_length),
        # "shoulder_width": float(body_data.shoulder_width),
        # "hip_joint_width": float(body_data.hip_joint_width),
        # "upper_body_length": float(body_data.upper_body_length),
        # "lower_body_length": float(body_data.lower_body_length),
        # "neck_length": float(body_data.neck_length)
    }

def get_default_body_info():
    """기본 체형 정보 반환"""
    return {
        "arm_type": "AVG",
        "femur_type": "AVG",
        "shoulder_type": "AVG",
        "hip_wide_type": "AVG",
        "upper_lower_body_type": "AVG",
        "upper_arm_length": 0.0,
        "forearm_length": 0.0,
        "femur_length": 0.0,
        "tibia_length": 0.0,
        "shoulder_width": 0.4,
        "hip_joint_width": 0.0,
        "upper_body_length": 0.0,
        "lower_body_length": 0.0,
        "neck_length": 0.0
    }
