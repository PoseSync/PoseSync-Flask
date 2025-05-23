from app.ai.body_analyzer.body_analyzer import BodyAnalyzer
from app.models import db, User, BodyType
from app.repositories.user_repository import insert_body_type
from app.models.body_data import BodyData
from datetime import datetime, timezone

# 체형 분석 AI 모델 인스턴스
body_analyzer = BodyAnalyzer()

def analyze_body_type(landmarks, height_cm):
    """
    3D 랜드마크와 키를 기반으로 체형 분석 수행
    """
    # 체형 분석 AI 모델 호출
    analysis_result = body_analyzer.analyze(landmarks, height_cm)
    
    return analysis_result

def save_body_length_data(phone_number: str, distances: dict):

    # phone_number → user_id 조회
    user = User.query.filter_by(phone_number=phone_number).first()
    if not user:
        raise ValueError("해당 사용자가 존재하지 않습니다")

    def avg(val1, val2):
        return round((val1 + val2) / 2, 2)

    # 기존 BodyData 존재 여부 확인
    existing_body_data = BodyData.query.filter_by(user_id=user.user_id).first()

    # 공통 계산 값
    upper_arm_length = avg(distances.get('left_upper_arm_length', 0), distances.get('right_upper_arm_length', 0))
    forearm_length = avg(distances.get('left_forearm_length', 0), distances.get('right_forearm_length', 0))
    femur_length = avg(distances.get('left_thigh_length', 0), distances.get('right_thigh_length', 0))
    tibia_length = avg(distances.get('left_calf_length', 0), distances.get('right_calf_length', 0))
    shoulder_width = distances.get('shoulder_width', 0)
    hip_joint_width = distances.get('hip_width', 0)

    if existing_body_data:
        # UPDATE
        existing_body_data.upper_arm_length = upper_arm_length
        existing_body_data.forearm_length = forearm_length
        existing_body_data.femur_length = femur_length
        existing_body_data.tibia_length = tibia_length
        existing_body_data.shoulder_width = shoulder_width
        existing_body_data.hip_joint_width = hip_joint_width
        existing_body_data.updated_at = datetime.now(timezone.utc)
    else:
        # INSERT
        new_body_data = BodyData(
            user_id=user.user_id,
            upper_arm_length=upper_arm_length,
            forearm_length=forearm_length,
            femur_length=femur_length,
            tibia_length=tibia_length,
            shoulder_width=shoulder_width,
            hip_joint_width=hip_joint_width,
            upper_body_length=None,
            lower_body_length=None,
            neck_length=None
        )
        db.session.add(new_body_data)

    db.session.commit()
    return True

def save_body_analysis_result(phone_number, analysis_result):
    """
    체형 분석 결과를 DB에 저장
    """
    try:
        # 사용자 조회
        user = User.query.filter_by(phone_number=phone_number).first()
        if not user:
            print(f"사용자를 찾을 수 없음: {phone_number}")
            return False
        
        # 기존 체형 정보 조회 또는 새로 생성
        body_type = BodyType.query.filter_by(user_id=user.user_id).first()
        if not body_type:
            body_type = BodyType(user_id=user.user_id)
        
        # 분석 결과에서 체형 정보 추출
        db_types = analysis_result.get('db_types', {})
        
        # 체형 정보 업데이트
        body_type.arm_type = db_types.get('arm_type', 'AVG')
        body_type.femur_type = db_types.get('femur_type', 'AVG')
        body_type.shoulder_type = db_types.get('shoulder_type', 'AVG')
        body_type.hip_wide_type = db_types.get('hip_wide_type', 'AVG')
        body_type.upper_lower_body_type = db_types.get('upper_lower_body_type', 'AVG')
        
        # DB에 저장
        db.session.add(body_type)
        db.session.commit()
        
        print(f"체형 분석 결과 저장 완료: {phone_number}")
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"체형 분석 결과 저장 중 오류: {e}")
        return False

def get_user_bone_lengths(phone_number: str) -> dict:
    """
    사용자의 DB에 저장된 뼈길이 데이터를 가져와서 
    exercise_data에서 사용하는 형식으로 변환하여 반환
    """
    try:
        # phone_number → user_id 조회
        user = User.query.filter_by(phone_number=phone_number).first()
        if not user:
            print(f"❌ 사용자를 찾을 수 없음: {phone_number}")
            return None

        # BodyData 조회
        body_data = BodyData.query.filter_by(user_id=user.user_id).first()
        if not body_data:
            print(f"❌ 사용자의 신체 데이터가 없음: {phone_number}")
            return None

        # exercise_data에서 사용하는 형식으로 변환
        bone_lengths = {
            "shoulder_width": float(body_data.shoulder_width),
            "hip_width": float(body_data.hip_joint_width),
            
            "left_upper_arm_length": float(body_data.upper_arm_length),
            "left_forearm_length": float(body_data.forearm_length),
            
            "right_upper_arm_length": float(body_data.upper_arm_length),
            "right_forearm_length": float(body_data.forearm_length),
            
            "left_thigh_length": float(body_data.femur_length),
            "left_calf_length": float(body_data.tibia_length),
            
            "right_thigh_length": float(body_data.femur_length),
            "right_calf_length": float(body_data.tibia_length)
        }
        
        # 모든 값이 0이 아닌지 확인
        if all(value == 0.0 for value in bone_lengths.values()):
            print(f"⚠️ 모든 뼈길이 데이터가 0임: {phone_number}")
            return None
            
        return bone_lengths
        
    except Exception as e:
        print(f"❌ DB 뼈길이 데이터 조회 중 오류: {e}")
        return None