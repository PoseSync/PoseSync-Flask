# 실측 기반 cm 단위 신체 길이 저장 테이블
# from datetime import datetime, UTC
from datetime import datetime, timezone

from app.models import db


class BodyDataCm(db.Model):
    __tablename__ = 'body_data_cm'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('user.user_id'), nullable=False)

    upper_arm_length_cm = db.Column(db.Float)     # cm 단위
    forearm_length_cm = db.Column(db.Float)
    shoulder_width_cm = db.Column(db.Float)
    femur_length_cm = db.Column(db.Float)
    tibia_length_cm = db.Column(db.Float)
    hip_joint_width_cm = db.Column(db.Float)
    upper_body_length_cm = db.Column(db.Float)
    lower_body_length_cm = db.Column(db.Float)
    neck_length_cm = db.Column(db.Float)

    # created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    # updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

         # 수정된 부분: UTC를 timezone.utc로 변경
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
