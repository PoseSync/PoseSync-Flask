from flask import Flask, jsonify, request
from flask_socketio import SocketIO
from app.sockets.user_socket import register_user_socket
from app.models import db, User  # models/__init__.py에서 정의한 db
import config
from sqlalchemy import inspect
from app.controllers.user_controller import save_body_data, body_data_bp
from app.services.user_info_service import save_phone_number_and_height, save_exercise_set_service, get_exercise_set_service, is_user_exist, get_next_exercise_set
from app.models.exercise_set import ExerciseSet

from app.models.user import User

from flask_cors import CORS

from app.controllers.body_analysis_controller import body_analysis_bp

from app.shared.global_state import is_exist


app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')
CORS(app, origins=["http://localhost:5173"])

 # DB 설정 적용
app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = config.SQLALCHEMY_TRACK_MODIFICATIONS

# Flask 인스턴스에 BluePrint 등록 => Controller에서 설정한 라우터를 사용할 수 있기 위해 필수
app.register_blueprint(body_data_bp)
app.register_blueprint(body_analysis_bp)

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

@app.route('/test', methods=['GET'])
def test():
    id = request.args.get('id')
    exercise_set = get_next_exercise_set(int(id))
    
    if exercise_set:
        result = {
            "id": exercise_set.id,
            "user_id": exercise_set.user_id,
            "exercise_type": exercise_set.exercise_type,
            "exercise_weight": exercise_set.exercise_weight,
            "target_count": exercise_set.target_count,
            "current_count": exercise_set.current_count,
            "is_finished": exercise_set.is_finished,
            "is_success": exercise_set.is_success,
            "routine_group": exercise_set.routine_group,
            "created_at": exercise_set.created_at.isoformat() if exercise_set.created_at else None,
            "updated_at": exercise_set.updated_at.isoformat() if exercise_set.updated_at else None
        }
        return jsonify(result), 200
    else:
        return jsonify({"error": "No data"}), 400


# 전화번호와 키로 User 생성하는 API
@app.route('/create_user', methods=['POST'])
def save_user():
    try:
        data = request.get_json()
        phone_number = data.get('phoneNumber')
        height = data.get('height')

        # 필수 값 검증
        if phone_number is None or height is None:
            return jsonify({"error": "phoneNumber and height are required"}), 400
        
        user = is_user_exist(data=data)
        if user:
            return jsonify({
                "message": "User 조회 성공",
                "user_id": user.user_id,
                "phone_number": user.phone_number,
                "height": str(user.height)
            }), 200
    
        user = save_phone_number_and_height(data=data)

        if user:
            return jsonify({
                "message": "User 저장 완료",
                "user_id": user.user_id,
                "phone_number": user.phone_number,
                "height": str(user.height)
            }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400   


@app.route('/save_exercise_set', methods=['POST'])
def save_exercise_set():
    data_list = request.get_json()

    if not isinstance(data_list, list):
        return jsonify({"error": "JSON body must be a list of exercise sets"}), 400

    results = []

    phone_number = data_list[0].get('phone_number')
    if not phone_number:
        return jsonify({"error": "Missing phone_number"}), 400

    # 유저 가져오기
    user = User.query.filter_by(phone_number=phone_number).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    # 🔸 routine_group을 한 번만 계산
    last_group = db.session.query(db.func.max(ExerciseSet.routine_group))\
        .filter_by(user_id=user.user_id).scalar()
    next_group = (last_group or 0) + 1

    for item in data_list:
        phone_number = item.get('phone_number')
        # exerciseType 명시
        exercise_name = item.get('exerciseType')
        exercise_weight = item.get('exercise_weight')
        exercise_cnt = item.get('exercise_cnt')

        if phone_number is None or exercise_name is None or exercise_weight is None or exercise_cnt is None:
            results.append({
                "phone_number": phone_number,
                "status": "error",
                "message": "Missing required data"
            })
            continue

        try:
            saved_set = save_exercise_set_service(item, user, next_group)  # 서비스 함수로 분리되어야 함
            results.append({
                "phone_number": phone_number,
                "status": "success",
                "exercise_set_id": saved_set.id
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            results.append({
                "phone_number": phone_number,
                "status": "error",
                "message": str(e)  # ✅ 이게 되어 있어야 함
            })
    db.session.commit()
    return jsonify(results), 201

@app.route('/get_exercise_set', methods=['GET'])
def get_exercise_set():
    phone_number = request.args.get('phone_number')

    if not phone_number:
        return jsonify({"error": "Missing phone_number"}), 400

    try:
        result = get_exercise_set_service(phone_number)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

# 낙상감지 후 클라이언트가 화면에서 나갈 때 호출
@app.route('/disconnect_call', methods=['POST'])
def disconnect_call():
    global is_exist, fall_detected
    is_exist = False
    fall_detected = False  # 낙상 감지 상태도 초기화
    print("########## is_exist = False로 변경 #############")

    return jsonify({
        "msg": "전화 서비스를 중단합니다."
    }), 200

if __name__ == '__main__':
    socketio.run(app, host='127.0.0.1', port=5001, debug=True, allow_unsafe_werkzeug=True)
