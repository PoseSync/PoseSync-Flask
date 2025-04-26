from . import db
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, UTC

# user 테이블 생성
class User(db.Model):
    __tablename__ = 'user'

    user_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)

    body_types = db.relationship('BodyType', backref='user', lazy=True)
    body_data = db.relationship('BodyData', backref='user', lazy=True)
    exercise_results = db.relationship('ExerciseResult', backref='user', lazy=True)