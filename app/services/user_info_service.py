from app.repositories.user_repository import create_user, insert_body_data, insert_body_type
from app.models import db
from app.models.body_type import BodyType

def save_user_and_body_data_and_body_type(data):
    try:
        phone_number = data.get('phoneNumber')
        
        if not phone_number:
            raise ValueError("phoneNumber는 필수입니다.")

        # user 저장
        user = create_user(phone_number)

        # body_data 저장
        body_data = insert_body_data(user.user_id, data)

        # body_type 저장 로직 시작
        arm_type = calculate_arm_type(body_data)
        femur_type = calculate_femur_type(body_data)
        upper_body_type = calculate_upper_body_type(body_data)
        tibia_type = calculate_tibia_type(body_data)
        shoulder_type = calculate_shoulder_type(body_data)
        hip_wide_type = calculate_hip_wide_type(body_data)
        lower_body_type = calculate_lower_body_type(body_data)
        torso_length_type = calculate_torso_length_type(body_data)

        # BodyType 객체 생성
        body_type = BodyType(
            user_id=user.user_id,
            arm_type=arm_type,
            femur_type=femur_type,
            tibia_type=tibia_type,
            shoulder_type=shoulder_type,
            hip_wide_type=hip_wide_type,
            upper_body_type=upper_body_type,
            lower_body_type=lower_body_type,
            torso_length_type=torso_length_type
        )

        insert_body_type(body_type)
        db.session.commit()

        return user.user_id

    except Exception as e:
        db.session.rollback()
        raise e

def calculate_torso_length_type(body_data):
    upper_body_length = body_data.upper_body_length
    lower_body_length = body_data.lower_body_length
    ratio = round(upper_body_length / lower_body_length, 2)
    if ratio >= 1.0:
        return 'LONG'
    elif ratio <= 0.89:
        return 'SHORT'
    else:
        return 'AVG'

def calculate_lower_body_type(body_data):
    lower_body_length = body_data.lower_body_length
    height = body_data.height
    ratio = round(lower_body_length / height, 2)
    if ratio >= 0.55:
        return 'LONG'
    elif ratio <= 0.49:
        return 'SHORT'
    else:
        return 'AVG'

def calculate_hip_wide_type(body_data):
    hip_joint_width = body_data.hip_joint_width
    height = body_data.height
    ratio = round(hip_joint_width / height, 2)
    if ratio >= 0.25:
        return 'WIDE'
    elif ratio <= 0.21:
        return 'NARROW'
    else:
        return 'AVG'

def calculate_shoulder_type(body_data):
    shoulder_width = body_data.shoulder_width
    height = body_data.height
    ratio = round(shoulder_width / height, 2)
    if ratio >= 0.27:
        return 'WIDE'
    elif ratio <= 0.22:
        return 'NARROW'
    else:
        return 'AVG'

def calculate_tibia_type(body_data):
    tibia_length = body_data.tibia_length
    height = body_data.height
    ratio = round(tibia_length / height, 2)
    if ratio >= 0.26:
        return 'LONG'
    elif ratio <= 0.22:
        return 'SHORT'
    else:
        return 'AVG'

def calculate_upper_body_type(body_data):
    upper_body_length = body_data.upper_body_length
    lower_body_length = body_data.lower_body_length
    ratio = round(upper_body_length / lower_body_length, 2)
    if ratio >= 1.0:
        return 'LONG'
    elif ratio <= 0.89:
        return 'SHORT'
    else:
        return 'AVG'

def calculate_arm_type(body_data):
    upper_arm_length = body_data.upper_arm_length
    forearm_length = body_data.forearm_length
    ratio = round(forearm_length / upper_arm_length, 2)
    if ratio <= 0.75:
        return 'LONG'
    elif ratio >= 0.95:
        return 'SHORT'
    else:
        return 'AVG'

def calculate_femur_type(body_data):
    femur_length = body_data.femur_length
    tibia_length = body_data.tibia_length
    ratio = round(femur_length / tibia_length, 2)
    if ratio < 1:
        return "LONG"
    elif ratio > 1.2:
        return "SHORT"
    else:
        return "AVG"