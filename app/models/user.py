from . import db
from flask_sqlalchemy import SQLAlchemy

# user 테이블 생성
class User(db.Model):
    __tablename__ = 'user'

    user_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    height = db.Column(db.Numeric(5, 2), nullable=False)

    body_types = db.relationship('BodyType', backref='user', lazy=True)
    body_data = db.relationship('BodyData', backref='user', lazy=True)
    exercise_set = db.relationship('ExerciseSet', backref='user', lazy=True)