from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# 아래는 모든 모델을 import해서 이곳에 등록
from .user import User
from .body_type import BodyType
from .body_data import BodyData
from .exercise_set import ExerciseSet