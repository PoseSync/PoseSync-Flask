from . import db
from datetime import datetime, UTC
from sqlalchemy import Enum

# body_type 테이블 생성
class BodyType(db.Model):
    __tablename__ = 'body_types'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('user.user_id'), nullable=False)

    arm_type = db.Column(Enum('LONG', 'AVG', 'SHORT', name='arm_enum'), nullable=True) # 상완길이 타입
    femur_type = db.Column(Enum('LONG', 'AVG', 'SHORT', name='femur_enum'), nullable=True)
    tibia_type = db.Column(Enum('LONG', 'AVG', 'SHORT', name='tibia_enum'), nullable=True)

    shoulder_type = db.Column(Enum('WIDE', 'AVG', 'NARROW', name='shoulder_enum'), nullable=True)
    hip_wide_type = db.Column(Enum('WIDE', 'AVG', 'NARROW', name='hip_enum'), nullable=True)

    upper_body_type = db.Column(Enum('LONG', 'AVG', 'SHORT', name='upper_enum'), nullable=True)
    lower_body_type = db.Column(Enum('LONG', 'AVG', 'SHORT', name='lower_enum'), nullable=True)
    torso_length_type = db.Column(Enum('LONG', 'AVG', 'SHORT', name='torso_enum'), nullable=True)
    neck_type = db.Column(Enum('LONG', 'AVG', 'SHORT', name='neck_enum'), nullable=True)
    leg_type = db.Column(Enum('LONG', 'AVG', 'SHORT', name='leg_enum'), nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
