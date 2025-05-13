from app.repositories.user_repository import create_user, insert_body_data, insert_body_type, save_record
from app.models import db
from app.models.body_type import BodyType
from app.services.squatService.squatService import squat_count
from app.models.exercise_result import ExerciseResult
from app.models.user import User


# User의 전화번호, 키 저장
def save_phone_number_and_height(data):
    height = data.get('height')
    phone_number = data.get('phoneNumber')

    # 이미 해당 데이터가 존재하는지 확인, 전화번호만 사용해서
    # first() => 조건을 만족하는 첫번째 record get
    user = User.query.filter_by(phone_number=phone_number).first()

    # 이미 해당 phone_number를 갖고 있는 User record가 있다면 무시
    if user:
        return
    
    # User 객체 저장 후 return
    new_user = User(phone_number=phone_number, height=height)
    db.session.add(new_user)
    db.session.commit()

    return new_user

# 운동이 중간에 종료됐을 때 record 저장
def save_record_failed_service(record):
    phone_number = record.phone_number

    # phone_number로 User 테이블 조회
    user = User.query.filter_by(phone_number=phone_number).first()

    if user is None:
        raise ValueError(f"해당 전화번호({phone_number})를 가진 사용자가 없습니다.")
    
    user_id = user.user_id

    # 2025/04/26 코멘트(성재)
    # ExerciseResult 객체 생성할 때 운동횟수는 Service 계층에서의 cnt 변수로 저장
    # 그런데 Service 계층에서 운동횟수를 각 운동 클래스마다 세고 있어서 어떤 운동의 운동횟수인지 저장하기 위해서 다수의 조건문 필요
    # 이게 최선인지 여러분들의 지혜가 필요
    # 스쿼트 운동 저장
    if (record.exercise_name == "squat"):
        exercise_result = ExerciseResult(
            user_id=user_id,
            exercise_name=record.exercise_name,
            count=squat_count,
            weight=record.exercise_weight
        )
        return save_record(exercise_result)
    return ""

# 운동이 성공적으로 끝났을 때 record 저장
def save_record_success_service(record):
    # record 안에 있는 phone_number 가져오기
    phone_number = record.phone_number

    # phone_number로 User 테이블 조회
    user = User.query.filter_by(phone_number=phone_number).first()

    if user is None:
        raise ValueError(f"해당 전화번호({phone_number})를 가진 사용자가 없습니다.")
    
    user_id = user.user_id

    # 여기서 ExerciseResult 객체 생성 후 Repository 계층으로 전달
    exercise_result = ExerciseResult(
        user_id=user_id,
        exercise_name=record.exercise_name,
        count=record.exercise_cnt,
        weight=record.exercise_weight
    )
    return save_record(exercise_result)


# user table, body_data, body_type 테이블에 데이터 저장
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