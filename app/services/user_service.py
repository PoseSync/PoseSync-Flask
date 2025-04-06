import numpy as np
from app.services.squat_util import get_theta, get_femur, height_hip_knee, get_pi
import math

def process_squat(data):
    
    landmarks = data.get("landmarks", [])

    # 양쪽 고관절 중심 좌표 계산
    left_hip = next((item for item in landmarks if item.get("id") == 23), None)
    right_hip = next((item for item in landmarks if item.get("id") == 24), None)

    h_center_x = (left_hip.get('x') + right_hip.get('x')) / 2
    h_center_z = (left_hip.get('z') + right_hip.get('z')) / 2

    # 왼쪽 무릎, 왼쪽 고관절, 오른쪽 무릎, 오른쪽 고관절 landmark를 매개변수로 넘겨준 후 theta 얻기
    left_knee = next((item for item in landmarks if item.get('id') == 25), None)
    right_knee = next((item for item in landmarks if item.get('id') == 26), None)
    theta = get_theta(left_hip, right_hip, left_knee, right_knee)

    # 대퇴골 길이, 양쪽 대퇴골 길이는 같다라는 가정 하에 왼쪽 무릎과 고관절만 매개변수로 넘겨줌
    femur = get_femur(left_hip, left_knee)

    # 고관절과 무릎 사이의 거리, 양쪽 고관절 높이가 같다라는 가정 하에 왼쪽 고관절과 왼쪽 무릎만 매개변수로 넘겨줌
    delta_y = height_hip_knee(left_hip, left_knee)

    # r 구하기
    r = math.sqrt((femur ** 2) - (delta_y ** 2))

    # pi 구하기
    pi = get_pi(left_hip, right_hip)

    # 라디안으로 변환
    pi_rad = math.radians(pi)
    theta_rad = math.radians(theta)

    # 각 무릎의 x, z 좌표 계산 (라디안 값으로 삼각함수 계산)
    left_knee_x = left_hip.get('x') + r * np.cos(pi_rad - (theta_rad / 2))
    left_knee_z = left_hip.get('z') + r * np.sin(pi_rad - (theta_rad / 2))

    right_knee_x = right_hip.get('x') + r * np.cos(pi_rad + (theta_rad / 2))
    right_knee_z = right_hip.get('z') + r * np.sin(pi_rad + (theta_rad / 2))

    for item in landmarks:
        if item['id'] == 25:
            item['x'] = left_knee_x
            item['z'] = left_knee_z
        elif item['id'] == 26:
            item['x'] = right_knee_x
            item['z'] = right_knee_z
            
    return data

