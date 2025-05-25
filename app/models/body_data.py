from . import db
# from datetime import datetime, UTC
from datetime import datetime, timezone

# body_data 테이블 생성
class BodyData(db.Model):
    __tablename__ = 'body_data'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('user.user_id'), nullable=False)


    upper_arm_length = db.Column(db.Numeric(5, 5))   # 상완길이
    forearm_length = db.Column(db.Numeric(5, 5))     # 전완길이
    femur_length = db.Column(db.Numeric(5, 5))       # 대퇴골 길이
    tibia_length = db.Column(db.Numeric(5, 5))       # 정강이 길이
    shoulder_width = db.Column(db.Numeric(5, 5))     # 어깨너비
    hip_joint_width = db.Column(db.Numeric(5, 5))    # 고관절너비
    upper_body_length = db.Column(db.Numeric(5, 2))
    lower_body_length = db.Column(db.Numeric(5, 2))
    neck_length = db.Column(db.Numeric(5, 2))

    # created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    # updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

         # 수정된 부분: UTC를 timezone.utc로 변경
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
