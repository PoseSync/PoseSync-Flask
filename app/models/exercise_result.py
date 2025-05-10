from . import db
# from datetime import datetime, UTC
from datetime import datetime, timezone

class ExerciseResult(db.Model):
    __tablename__ = 'exercise_result'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    
    user_id = db.Column(db.BigInteger, db.ForeignKey('user.user_id'), nullable=False)  # 외래 키

    # date = db.Column(db.DateTime, default=datetime.now(UTC), nullable=False)  # 현재 날짜 기본값
    date = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)  # UTC 시간을 올바르게 설정
    exercise_name = db.Column(db.String(50), nullable=False)
    count = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Float, nullable=False)  # 무게는 선택사항으로 nullable=True -> # 2025/04/27 무게는 0도 입력받아야 하므로 False로 설정