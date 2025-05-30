from app.repositories.user_repository import create_user, insert_body_data, insert_body_type
from app.models import db
from app.models.body_type import BodyType
from app.models.user import User
from app.models.exercise_set import ExerciseSet

# 전화번호로 User를 조회해서 height 반환하는 함수
def get_height_service(phone_number):
    print(f'get_height_service 호출됨 - 전화번호: {phone_number}')

    try:
        user = User.query.filter_by(phone_number=phone_number).first()
        print(f'사용자 조회 결과: {user}')

        if not user:
            print(f'❌ 사용자를 찾을 수 없음: {phone_number}')
            raise ValueError(f"User not found: {phone_number}")

        print(f'사용자 키: {user.height}')
        return user.height

    except Exception as e:
        print(f'❌ get_height_service 예외: {e}')
        raise e


def get_exercise_set_service(phone_number):
    user = User.query.filter_by(phone_number=phone_number).first()
    if not user:
        raise ValueError("User not found")

    # 가장 큰 routine_group 값 조회
    last_group = db.session.query(db.func.max(ExerciseSet.routine_group))\
        .filter_by(user_id=user.user_id).scalar()

    if last_group is None:
        raise ValueError("No exercise sets found")

    sets = ExerciseSet.query.filter_by(user_id=user.user_id, routine_group=last_group).all()

    return {
        "phone_number": phone_number,
        "routine_group": last_group,
        "sets": [
            {
                "id": s.id,
                "exercise_type": s.exercise_type,
                "exercise_weight": s.exercise_weight,
                "target_count": s.target_count,
                "current_count": s.current_count,
                "is_finished": s.is_finished,
                "is_success": s.is_success,
                "routine_group": s.routine_group,
                "created_at": s.created_at.isoformat(),
            }
            for s in sets
        ]
    }

# 다음 운동세트를 가져오는 함수
def get_next_exercise_set(current_id):
    # 현재 ExerciseSet 객체 조회
    current_set = ExerciseSet.query.filter_by(id=current_id).first()

    # 같은 routine_group이고, id가 현재 id보다 1 큰 객체 조회
    next_set = ExerciseSet.query.filter_by(
        routine_group=current_set.routine_group
    ).filter(
        ExerciseSet.id == current_id + 1
    ).first()

    return next_set  # 없으면 자동으로 None 반환

# ExerciseSet 엔티티를 받아 UPDATE 한 후 저장하는 함수
def save_updated_exercise_set(exercise_set:ExerciseSet):
    db.session.add(exercise_set)
    db.session.commit()

    routine_group = exercise_set.routine_group
    
    # 현재 끝낸 운동과 같은 routine_group 값을 갖는 exercise_set 객체들을 담는 List
    all_exercise_set = ExerciseSet.query.filter_by(routine_group=routine_group).all()

    # is_finished=False인 요소 중에서 가장 나중에 들어온 데이터 찾기 (created_at 가장 작은 값)
    # 가장 먼저 저장된(is_finished=False) 데이터 → 과거
    earliest_unfinished = min(
        (es for es in all_exercise_set if not es.is_finished), 
        key=lambda x: x.created_at,
        default=None
    )

    # 해당 요소의 인덱스 가져오기
    if earliest_unfinished:
        latest_index = all_exercise_set.index(earliest_unfinished)
    else:
        latest_index = -1  # 해당 조건을 만족하는 요소가 없는 경우

    return exercise_set, latest_index

# 전화번호로 해당 User와 가장 가까운 ExerciseSet 반환 함수
def get_exercise_set_with_phone_number(phone_number):
    user = User.query.filter_by(phone_number=phone_number).first()

    # 최신 순으로 정렬  
    # 가장 최근 1개
    exercise_set = ExerciseSet.query.filter_by(user_id=user.user_id, is_finished=False).order_by(ExerciseSet.created_at.asc()).first()

    return exercise_set

def is_user_exist(data):
    phone_number = data.get('phoneNumber')

    user = User.query.filter_by(phone_number=phone_number).first()
    if user:
        return user

# 운동 세트 정보 저장
def save_exercise_set_service(data, user, routine_group):
    exercise_type = data['exerciseType']
    weight = data['exercise_weight']
    count = data['exercise_cnt']

    new_set = ExerciseSet(
        user_id=user.user_id,
        exercise_type=exercise_type,
        exercise_weight=weight,
        target_count=count,
        routine_group=routine_group
    )

    db.session.add(new_set)
    db.session.flush()
    return new_set

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
        shoulder_type = calculate_shoulder_type(body_data)
        hip_wide_type = calculate_hip_wide_type(body_data)
        upper_lower_body_type = calculate_upper_lower_body_type(body_data)

        # BodyType 객체 생성
        body_type = BodyType(
            user_id=user.user_id,
            arm_type=arm_type,
            femur_type=femur_type,
            shoulder_type=shoulder_type,
            hip_wide_type=hip_wide_type,
            upper_lower_body_type=upper_lower_body_type
        )

        insert_body_type(body_type)
        db.session.commit()

        return user.user_id

    except Exception as e:
        db.session.rollback()
        raise e


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

def calculate_upper_lower_body_type(body_data):
    upper_body_length = body_data.upper_body_length
    lower_body_length = body_data.lower_body_length
    ratio = round(upper_body_length / lower_body_length, 2)
    if ratio >= 1.0:
        return 'LONG'
    elif ratio <= 0.89:
        return 'SHORT'
    else:
        return 'AVG'