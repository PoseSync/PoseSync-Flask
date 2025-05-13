from flask import Flask, jsonify, request
from flask_socketio import SocketIO
from app.sockets.user_socket import register_user_socket
from app.models import db  # models/__init__.py에서 정의한 db
import config
from sqlalchemy import inspect
from app.controllers.user_controller import save_body_data, body_data_bp


app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')

 # DB 설정 적용
app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = config.SQLALCHEMY_TRACK_MODIFICATIONS

# Flask 인스턴스에 BluePrint 등록 => Controller에서 설정한 라우터를 사용할 수 있기 위해 필수
app.register_blueprint(body_data_bp)

# SQLAlchemy 초기화
db.init_app(app)

# 테이블 생성 (앱 컨텍스트 내에서)
with app.app_context():
    try:
        db.create_all()
        inspector = inspect(db.engine)
        print("📂 현재 DB 테이블 목록:", inspector.get_table_names())
    except Exception as e:
        print("❌ 테이블 생성 중 오류:", e)

register_user_socket(socketio)

# 테스트 용 라우터
@app.route('/')
def home():
    return 'Flask + SQLAlchemy + MySQL + WebSocket 실행 중!'



if __name__ == '__main__':
    socketio.run(app, host='127.0.0.1', port=5001, debug=True, allow_unsafe_werkzeug=True)
