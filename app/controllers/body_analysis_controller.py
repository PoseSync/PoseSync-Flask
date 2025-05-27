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
        print('🔍 [STEP 0] API 시작 - analyze_body 함수 진입')

        data = request.get_json()
        print(f'🔍 [STEP 1] 요청 데이터 파싱 완료: {type(data)}, 키 개수: {len(data) if data else 0}')

        # 랜드마크 받아오기
        landmarks = data.get('landmarks', [])
        # 월드 랜드마크 받아오기
        world_landmarks = data.get('world_landmarks', [])
        print(f'🔍 [STEP 2] 랜드마크 데이터 추출: {len(landmarks)}개의 랜드마크')

        # 전화번호
        phone_number = data.get('phoneNumber')
        print(f'🔍 [STEP 3] 전화번호 추출: {phone_number}')

        print('1. 여기까지됨')

        # 필수 입력값 검증
        if not landmarks:
            print('❌ [ERROR] 랜드마크 데이터가 비어있음')
            return jsonify({"success": False, "error": "랜드마크 데이터가 없습니다"}), 400
        print('2. 여기까지됨')

        # 전화번호로 User의 키 GET
        print('🔍 [STEP 4] get_height_service 호출 시작')
        try:
            height_raw = get_height_service(phone_number=phone_number)
            print(f'🔍 [STEP 4-1] get_height_service 결과: {height_raw} (타입: {type(height_raw)})')

            height = float(height_raw)
            print(f'🔍 [STEP 4-2] 키 변환 완료: {height}cm')
        except Exception as e:
            print(f'❌ [ERROR STEP 4] get_height_service 오류: {str(e)}')
            raise e

        # 10개의 프레임들의 평균값을 갖는 새로운 landmarks 리스트 생성
        print('🔍 [STEP 5] average_landmarks 호출 시작')
        try:
            new_landmarks = average_landmarks(landmarks)
            new_world_landmarks = average_landmarks(world_landmarks)
            print(f'🔍 [STEP 5-1] new_landmarks : {new_landmarks} new_world_landmarks : {new_world_landmarks}')

        except Exception as e:
            print(f'❌ [ERROR STEP 5] average_landmarks 오류: {str(e)}')
            raise e

        # 체형 분석 수행
        print('🔍 [STEP 6] analyze_body_type 호출 시작')
        try:
            # 월드 랜드마크로 체형 분석
            analysis_result = analyze_body_type(new_world_landmarks, height)
            print(f'🔍 [STEP 6-1] analyze_body_type 완료: {type(analysis_result)}')
            print(
                f'🔍 [STEP 6-2] 분석 결과 키들: {list(analysis_result.keys()) if isinstance(analysis_result, dict) else "dict가 아님"}')
        except Exception as e:
            print(f'❌ [ERROR STEP 6] analyze_body_type 오류: {str(e)}')
            raise e

        # N개의 프레임 Landmarks 평균값 정규화
        print('🔍 [STEP 7] process_pose_landmarks 호출 시작')
        try:
            transformed_landmarks, transform_data = process_pose_landmarks(new_landmarks)
            print(f'🔍 [STEP 7-1] process_pose_landmarks 완료: {len(transformed_landmarks)}개의 변환된 랜드마크')
        except Exception as e:
            print(f'❌ [ERROR STEP 7] process_pose_landmarks 오류: {str(e)}')
            raise e

        print('🔍 [STEP 8] 랜드마크 이름 매핑 시작')
        try:
            for i, lm in enumerate(transformed_landmarks):
                lm['name'] = PoseLandmark(lm['id']).name
                if i < 3:  # 처음 3개만 로그
                    print(f'🔍 [STEP 8-{i}] 랜드마크 {lm["id"]} -> {lm["name"]}')
            print(f'🔍 [STEP 8-완료] {len(transformed_landmarks)}개 랜드마크 이름 매핑 완료')
        except Exception as e:
            print(f'❌ [ERROR STEP 8] 랜드마크 이름 매핑 오류: {str(e)}')
            raise e

        print('🔍 [STEP 9] calculate_named_linked_distances 호출 시작')
        try:
            current_distances = calculate_named_linked_distances(transformed_landmarks, connections)
            print(
                f'🔍 [STEP 9-1] calculate_named_linked_distances 완료: {len(current_distances) if current_distances else 0}개의 거리')
        except Exception as e:
            print(f'❌ [ERROR STEP 9] calculate_named_linked_distances 오류: {str(e)}')
            raise e

        print('🔍 [STEP 10] map_distances_to_named_keys 호출 시작')
        try:
            current_distances = map_distances_to_named_keys(current_distances, bone_name_map)
            print(
                f'🔍 [STEP 10-1] map_distances_to_named_keys 완료: {len(current_distances) if current_distances else 0}개의 매핑된 거리')
            distances = current_distances
        except Exception as e:
            print(f'❌ [ERROR STEP 10] map_distances_to_named_keys 오류: {str(e)}')
            raise e

        # 결과 DB에 저장 (전화번호가 있는 경우)
        if phone_number:
            print('🔍 [STEP 11] DB 저장 시작')
            try:
                save_success = save_body_analysis_result(phone_number, analysis_result)
                print(f'🔍 [STEP 11-1] save_body_analysis_result 완료: {save_success}')

                save_body_length_data(phone_number, distances)
                print(f'🔍 [STEP 11-2] save_body_length_data 완료')

                analysis_result["saved_to_db"] = save_success
            except Exception as e:
                print(f'❌ [ERROR STEP 11] DB 저장 오류: {str(e)}')
                raise e
        else:
            print('🔍 [STEP 11] 전화번호 없음 - DB 저장 건너뜀')

        print('✅ [SUCCESS] 모든 단계 완료 - 결과 반환')
        return jsonify({"success": True, "result": analysis_result}), 200

    except Exception as e:
        print(f'💥 [FATAL ERROR] 예외 발생: {str(e)}')
        print(f'💥 [FATAL ERROR] 예외 타입: {type(e).__name__}')
        import traceback
        print(f'💥 [FATAL ERROR] 스택 트레이스:\n{traceback.format_exc()}')
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
