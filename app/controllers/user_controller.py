from app.services.squatService.squatService import process_squat
from app.services.sholderPressService.sholderPressService import process_dumbbell_sholderPress
from app.services.user_info_service import save_user_and_body_data_and_body_type, save_record_success_service, save_record_failed_service
from flask import Blueprint, jsonify, request


def handle_data_controller(data):
    if data.get('exerciseType') == 'squat':
        # 스쿼트 로직 처리 서비스에 data 넘겨주고 비즈니스 로직 처리 위임
        return process_squat(data)
    elif data.get('exerciseType') == 'dumbel_sholder_press':
        result =  process_dumbbell_sholderPress(data)
        return result

# 운동 성공적 종료됐을 때 DB에 저장하는 컨트롤러 함수
def save_record_success_controller(record):
    return save_record_success_service(record)

# 운동 중단 종료됐을 때 DB에 저장하는 컨트롤러 함수
def save_record_failed_controller(record):
    return save_record_failed_service(record)
    

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
