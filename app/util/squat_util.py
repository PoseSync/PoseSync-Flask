import numpy as np
from app.util.math_util import normalize_vector
import math

# theta 값 구하기
def get_theta(left_hip, right_hip, left_knee, right_knee):
    # 고관절과 무릎을 잇는 방향벡터 구하기
    left_vector = np.array([
    left_knee.get('x') - left_hip.get('x'),
    left_knee.get('y') - left_hip.get('y'),
    left_knee.get('z') - left_hip.get('z')
    ])

    right_vector = np.array([
    right_knee.get('x') - right_hip.get('x'),
    right_knee.get('y') - right_hip.get('y'),
    right_knee.get('z') - right_hip.get('z')
    ])

    # 각 벡터 정규화
    left_vector_normalized = normalize_vector(left_vector)
    right_vector_normalized = normalize_vector(right_vector)

    # 정규화된 벡터로 내적 후 theta 산출
    dot_product = np.dot(left_vector_normalized, right_vector_normalized)
    dot_product = np.clip(dot_product, -1.0, 1.0)  # 안정성 확보

    theta_rad = np.arccos(dot_product)
    theta_deg = np.degrees(theta_rad)
    return theta_deg

# 대퇴골 길이 L 구하기
def get_femur(left_hip, left_knee):
    x_result = (left_knee.get('x') - left_hip.get('x')) ** 2
    y_result = (left_knee.get('y') - left_hip.get('y')) ** 2
    z_result = (left_knee.get('z') - left_hip.get('z')) ** 2
    result = math.sqrt(x_result + y_result + z_result)
    return result

# 고관절과 무릎 사이의 거리
def height_hip_knee(left_hip, left_knee):
    result = left_hip.get('y') - left_knee.get('y')
    return result

def get_pi(left_hip, right_hip):
    # 엉덩이 라인 벡터 (오른쪽 - 왼쪽)
    vector = np.array([
        right_hip['x'] - left_hip['x'],
        right_hip['y'] - left_hip['y'],
        right_hip['z'] - left_hip['z']
    ])

    # y축 단위 벡터
    y_axis = np.array([0, 1, 0])

    # 바라보는 방향 = 엉덩이 라인 × y축
    facing_direction = np.cross(vector, y_axis)
    facing_direction_normalized = normalize_vector(facing_direction)

     # 카메라가 보는 방향 (z축 -1)
    camera_direction = np.array([0, 0, -1])

    # 내적 및 각도 계산
    dot = np.dot(facing_direction_normalized, camera_direction)
    dot = np.clip(dot, -1.0, 1.0)

    angle_rad = np.arccos(dot)
    angle_deg = np.degrees(angle_rad)

    return angle_deg
