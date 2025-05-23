from flask import Blueprint, request, jsonify
from app.services.user_info_service import get_height_service
from app.services.body_service.body_analysis_service import analyze_body_type, save_body_analysis_result, save_body_length_data
from app.util.pose_transform import process_pose_landmarks
from app.util.calculate_landmark_distance import connections, calculate_named_linked_distances, \
    map_distances_to_named_keys, bone_name_map
from app.util.pose_landmark_enum import PoseLandmark

# 블루프린트 생성
body_analysis_bp = Blueprint('body_analysis', __name__, url_prefix='/api/body-analysis')

@body_analysis_bp.route('/analyze', methods=['POST'])
def analyze_body():
    """체형 분석 API 엔드포인트"""
    try:
        data = request.get_json()
        # 랜드마크 10개 받아오기
        landmarks = data.get('landmarks', [])
        # 전화번호
        phone_number = data.get('phoneNumber')

        print('1. 여기까지됨')

        # 필수 입력값 검증
        if not landmarks:
            return jsonify({"success": False, "error": "랜드마크 데이터가 없습니다"}), 400
        print('2. 여기까지됨')

        # 전화번호로 User의 키 GET
        height = float(get_height_service(phone_number=phone_number))
        # 10개의 프레임들의 평균값을 갖는 새로운 landmarks 리스트 생성
        print('❌❌❌ 여기까지됨')
        new_landmarks = average_landmarks(landmarks)

        print('3. 여기까지됨')
        # 체형 분석 수행
        analysis_result = analyze_body_type(new_landmarks, height)

        # 10개의 프레임 Landmarks 평균값 정규화
        transformed_landmarks, transform_data = process_pose_landmarks(new_landmarks)
        for lm in transformed_landmarks:
            lm['name'] = PoseLandmark(lm['id']).name
        print('4. 여기까지됨')
        current_distances = calculate_named_linked_distances(transformed_landmarks, connections)
        current_distances = map_distances_to_named_keys(current_distances, bone_name_map)
        distances = current_distances
        print('5. 여기까지됨')
        # 결과 DB에 저장 (전화번호가 있는 경우)
        if phone_number:
            save_success = save_body_analysis_result(phone_number, analysis_result)
            save_body_length_data(phone_number, distances)
            analysis_result["saved_to_db"] = save_success
        
        return jsonify({"success": True, "result": analysis_result}), 200
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    
def average_landmarks(landmarks_sequence):
    """
    landmarks_sequence: 길이가 10인 리스트, 각 요소는 33개의 landmark 딕셔너리
    반환값: id별 평균 좌표 리스트 (총 33개)
    """
    from collections import defaultdict

    # 초기화
    coord_sum = defaultdict(lambda: {"x": 0.0, "y": 0.0, "z": 0.0, "count": 0})

    # 프레임 순회
    for frame in landmarks_sequence:
        for lm in frame:
            lm_id = lm["id"]
            coord_sum[lm_id]["x"] += lm["x"]
            coord_sum[lm_id]["y"] += lm["y"]
            coord_sum[lm_id]["z"] += lm["z"]
            coord_sum[lm_id]["count"] += 1

    # 평균 계산
    result = []
    for lm_id in range(33):
        if coord_sum[lm_id]["count"] > 0:
            count = coord_sum[lm_id]["count"]
            result.append({
                "id": lm_id,
                "x": coord_sum[lm_id]["x"] / count,
                "y": coord_sum[lm_id]["y"] / count,
                "z": coord_sum[lm_id]["z"] / count,
            })
        # else:
        #     result.append({
        #         "id": lm_id,
        #         "x": 0.0,
        #         "y": 0.0,
        #         "z": 0.0,
        #     })

    return result
