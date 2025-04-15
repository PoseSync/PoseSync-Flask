from app.services.user_service import process_squat, process_dumbel_sholderPress


def handle_data_controller(data):
    if data.get('exerciseType') == 'squat':
        # 스쿼트 로직 처리 서비스에 data 넘겨주고 비즈니스 로직 처리 위임
        result = process_squat(data)
    elif data.get('exerciseType') == 'dumbel_sholder_press':
        result =  process_dumbel_sholderPress(data)

    return result