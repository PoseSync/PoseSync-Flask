from . import db
# from datetime import datetime, UTC
from datetime import datetime, timezone

class ExerciseSet(db.Model):
    __tablename__ = 'exercise_set'

    # 기본키
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)

    # User를 참조하는 외래키
    user_id = db.Column(db.BigInteger, db.ForeignKey('user.user_id'), nullable=False)

    # 운동 이름
    exercise_type = db.Column(db.String(50), nullable=False)

    # 운동 무게
    exercise_weight = db.Column(db.Float, nullable=False)  # 무게는 선택사항으로 nullable=True -> # 2025/04/27 무게는 0도 입력받아야 하므로 False로 설정

    # 운동 횟수
    target_count = db.Column(db.Integer, nullable=False)

    # 현재 운동 횟수, 기본값 = 0
    current_count = db.Column(db.Integer, nullable=False, default = 0)

    # 운동 끝남 여부, 기본값 False
    is_finished = db.Column(db.Boolean, nullable=False, default=False)

    # 운동 성공 여부, 기본값 False
    is_success = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))