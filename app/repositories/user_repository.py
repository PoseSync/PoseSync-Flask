from app.models import db
from app.models.user import User
from app.models.body_data import BodyData

def create_user(phone_number):
    # 엔티티 생성
    user = User(phone_number=phone_number)

    # INSERT문 생성
    db.session.add(user)

    # DB에 쿼리 날림
    db.session.flush()

    return user

def insert_body_data(user_id, data):
    new_data = BodyData(
        user_id=user_id,
        height=data['height'],
        weight=data['weight'],
        upper_arm_length=data['upper_arm_length'],
        forearm_length=data['forearm_length'],
        femur_length=data['femur_length'],
        tibia_length=data['tibia_length'],
        shoulder_width=data['shoulder_width'],
        hip_joint_width=data['hip_joint_width'],
        upper_body_length=data['upper_body_length'],
        lower_body_length=data['lower_body_length'],
        neck_length=data['neck_length']
    )
    db.session.add(new_data)
    db.session.flush()
    return new_data

def insert_body_type(data):
    db.session.add(data)
    return data
