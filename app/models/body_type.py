from . import db
# from datetime import datetime, UTC
from datetime import datetime, timezone
from sqlalchemy import Enum

# 상대좌표계 점-점 거리 저장용
class BodyType(db.Model):
    __tablename__ = 'body_type'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('user.user_id'), nullable=False)

    arm_type = db.Column(Enum('LONG', 'AVG', 'SHORT', name='arm_enum'), nullable=True) # 상완-전완 비율 타입
    femur_type = db.Column(Enum('LONG', 'AVG', 'SHORT', name='femur_enum'), nullable=True) # 대퇴골-정강이 비율 타입


    shoulder_type = db.Column(Enum('WIDE', 'AVG', 'NARROW', name='shoulder_enum'), nullable=True) # 어깨 : 신장 비율 타입
    hip_wide_type = db.Column(Enum('WIDE', 'AVG', 'NARROW', name='hip_enum'), nullable=True) # 고관절 너비 : 신장 비율 타입

    upper_lower_body_type = db.Column(Enum('LONG', 'AVG', 'SHORT', name='upper_enum'), nullable=True) # 상체-하체 비율 타입


    # created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    # updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

     # 수정된 부분: UTC를 timezone.utc로 변경
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
