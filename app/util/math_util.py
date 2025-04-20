import math

import numpy as np

# 벡터 정규화 함수
def normalize_vector(v):
    norm = np.linalg.norm(v)
    return v / norm if norm != 0 else v


#두 벡터사이 각도를 degree 단위로 반환
def vector_angle_deg(v1: np.ndarray, v2: np.ndarray) -> float:
    """
    두 벡터 v1, v2 사이의 각도를 degree 단위로 반환
    """
    # v1 벡터 정규화 (길이를 1로 만든 방향벡터)
    v1_norm = v1 / np.linalg.norm(v1) if np.linalg.norm(v1) != 0 else v1
    # v2 벡터 정규화
    v2_norm = v2 / np.linalg.norm(v2) if np.linalg.norm(v2) != 0 else v2
    # 두 벡터의 내적 계산
    dot = np.dot(v1_norm, v2_norm)
    # arccos 계산 오류 방지를 위해 -1.0 ~ 1.0 사이로 클리핑
    dot = np.clip(dot, -1.0, 1.0)
    # 내적의 arccos를 통해 두 벡터 사이의 라디안 각도 구함
    angle_rad = np.arccos(dot)
    # 라디안 → degree 변환 후 반환
    return np.degrees(angle_rad)



def vector_angle_deg(v1, v2):
    """
    두 벡터 사이의 각도를 (도 단위)로 계산합니다.
    - 입력: np.ndarray 또는 list [x, y, z] 두 개
    - 출력: 각도 (degree)
    - 용도: 관절 사이 각도 계산 (ex. 팔꿈치, 무릎 등)
    """
    v1 = normalize_vector(v1)
    v2 = normalize_vector(v2)
    dot = np.dot(v1, v2)
    dot = np.clip(dot, -1.0, 1.0)
    angle_rad = math.acos(dot)
    return math.degrees(angle_rad)

def project_length_on_xz(length, delta_y):
    """
    수직(y축) 방향 차이를 제외한 xz 평면상 거리(투영 길이)를 구합니다.
    - 입력: 전체 길이 (예: 팔 길이), y축 차이(delta_y)
    - 출력: xz 평면 투영 거리
    - 용도: 수직 거리 외의 이동거리 계산 (팔꿈치, 손목 위치 계산 등)
    - 사용 예: shoulder → elbow 방향이 고정되어 있을 때 elbow의 xz 위치 보정
    """
    return math.sqrt(max(length ** 2 - delta_y ** 2, 0))

def get_rotated_offset(length, angle_deg):
    """
    주어진 거리(length)를 특정 각도(angle_deg)에 따라 x, z축으로 나누어 반환합니다.
    - 입력: 거리 (float), 각도 (도 단위)
    - 출력: (dx, dz) 튜플
    - 용도: 특정 방향으로 길이만큼 이동할 좌표 계산
    - 사용 예: 어깨를 기준으로 팔꿈치를 앞 방향으로 고정시키는 경우
    """
    angle_rad = math.radians(angle_deg)
    dx = math.cos(angle_rad) * length
    dz = math.sin(angle_rad) * length
    return dx, dz

def clamp_min_elbow_y(shoulder_y, arm_length, min_angle_deg):
    """
    팔꿈치가 최소 각도를 유지할 수 있도록 Y값을 보정합니다.
    - 입력: 어깨 높이, 팔 길이, 최소 유지 각도
    - 출력: 보정된 elbow_y
    - 용도: 팔이 너무 내려가 각도가 무너질 경우 보정
    - 사용 예: 덤벨 숄더프레스에서 elbow_min_angle 유지
    """
    min_rad = math.radians(min_angle_deg)
    min_delta_y = math.cos(min_rad) * arm_length
    return shoulder_y + min_delta_y