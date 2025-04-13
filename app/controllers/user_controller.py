from app.services.user_service import process_squat

def handle_data_controller(data):
    if data.get('exerciseType') == 'squat':
        # 스쿼트 로직 처리 서비스에 data 넘겨주고 비즈니스 로직 처리 위임
        result = process_squat(data)

    return result