from app.services.user_service import process_squat
from app.services.user_info_service import save_user_and_body_data_and_body_type
from flask import Blueprint, jsonify, request

def handle_data_controller(data):
    if data.get('exerciseType') == 'squat':
        # 스쿼트 로직 처리 서비스에 data 넘겨주고 비즈니스 로직 처리 위임
        result = process_squat(data)

    return result

# Blueprint 등록
# 'body_data' => BluePrint ID(식별자) 역할
# 이 파일의 파이썬 모듈명. Flask 내부에서 import 경로 추적에 사용
# 공통 URL 경로 ex) /body-data/save
body_data_bp = Blueprint('body_data', __name__, url_prefix='/body-data')

@body_data_bp.route('/save', methods=['POST'])
def save_body_data():
    try:
        data = request.get_json()
        user_id = save_user_and_body_data_and_body_type(data)
        return jsonify({"message": "User + BodyData 저장 완료", "user_id": user_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
