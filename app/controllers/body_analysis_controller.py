from flask import Blueprint, request, jsonify
from app.services.body_service.body_analysis_service import analyze_body_type, save_body_analysis_result

# 블루프린트 생성
body_analysis_bp = Blueprint('body_analysis', __name__, url_prefix='/api/body-analysis')

@body_analysis_bp.route('/analyze', methods=['POST'])
def analyze_body():
    """체형 분석 API 엔드포인트"""
    try:
        data = request.get_json()
        landmarks = data.get('landmarks', [])
        height_cm = data.get('height', 170)  # 기본 키 설정
        phone_number = data.get('phoneNumber')
        
        # 필수 입력값 검증
        if not landmarks:
            return jsonify({"success": False, "error": "랜드마크 데이터가 없습니다"}), 400
        
        if not height_cm:
            return jsonify({"success": False, "error": "키 정보가 없습니다"}), 400
        
        # 체형 분석 수행
        analysis_result = analyze_body_type(landmarks, height_cm)
        
        # 결과 DB에 저장 (전화번호가 있는 경우)
        if phone_number:
            save_success = save_body_analysis_result(phone_number, analysis_result)
            analysis_result["saved_to_db"] = save_success
        
        return jsonify({"success": True, "result": analysis_result}), 200
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500