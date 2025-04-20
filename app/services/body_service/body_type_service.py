from app.models.user import User
from app.models.body_type import BodyType



# 상완 체형타이 가져옴
def get_user_arm_type(phone_number):
    user = User.query.filter_by(phone_number=phone_number).first()
    if not user:
        raise Exception("사용자 정보를 찾을 수 없습니다")


    body_type = BodyType.query.filter_by(user_id=user.user_id).first()
    if not body_type or not body_type.arm_type:
        raise Exception("사용자의 상완 타입 정보가 없습니다")

    return body_type.arm_type  # 'LONG' / 'AVG' / 'SHORT'
