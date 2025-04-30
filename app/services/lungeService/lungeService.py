import math
from app.util.pose_landmark_enum import PoseLandmark

# 운동 상태 추적용 전역 변수
previous_hip_y = None    # 이전 골반 높이
is_descending = False    # 내려가는 중인지 여부
min_hip_y = None         # 최저 골반 높이
reached_bottom = False   # 최저점 도달 여부
completed_reps = 0       # 완료한 런지 횟수

# 초기 자세 저장용 전역 변수
initial_pose = {
    "left_shoulder_hip_diff": None,
    "right_shoulder_hip_diff": None
}

# 세 점으로 관절 각도 계산
def calculate_angle(a, b, c):
    ab = math.sqrt((b['x'] - a['x'])**2 + (b['y'] - a['y'])**2)
    bc = math.sqrt((b['x'] - c['x'])**2 + (b['y'] - c['y'])**2)
    ac = math.sqrt((c['x'] - a['x'])**2 + (c['y'] - a['y'])**2)

    if ab == 0 or bc == 0:
        return 0.0

    cos_theta = (ab**2 + bc**2 - ac**2) / (2 * ab * bc)
    cos_theta = min(1.0, max(-1.0, cos_theta))
    angle = math.degrees(math.acos(cos_theta))

    return angle

# ✅ 1. 초기 자세 저장 함수
# 이 함수는 socket 통신 처음 시작할 때 호출
def save_initial_pose(data):
    global initial_pose

    landmarks = data.get("landmarks", [])

    if not landmarks:
        raise ValueError("landmarks 데이터가 없습니다")

    left_shoulder = landmarks[PoseLandmark.LEFT_SHOULDER]
    right_shoulder = landmarks[PoseLandmark.RIGHT_SHOULDER]
    left_hip = landmarks[PoseLandmark.LEFT_HIP]
    right_hip = landmarks[PoseLandmark.RIGHT_HIP]

    # 초기 어깨-골반 x좌표 차이 저장
    initial_pose["left_shoulder_hip_diff"] = left_shoulder['x'] - left_hip['x']
    initial_pose["right_shoulder_hip_diff"] = right_shoulder['x'] - right_hip['x']

    print(f"✅ 초기 자세 저장 완료: {initial_pose}")

# ✅ 2. 운동 중 자세 교정 + 런지 과정 분석
def correct_lunge_pose_for_lunge(data):
    global previous_hip_y, is_descending, min_hip_y, reached_bottom, completed_reps

    landmarks = data.get("landmarks", [])

    if not landmarks:
        return data

    # 주요 포인트
    left_hip = landmarks[PoseLandmark.LEFT_HIP]
    right_hip = landmarks[PoseLandmark.RIGHT_HIP]
    left_knee = landmarks[PoseLandmark.LEFT_KNEE]
    right_knee = landmarks[PoseLandmark.RIGHT_KNEE]
    left_ankle = landmarks[PoseLandmark.LEFT_ANKLE]
    right_ankle = landmarks[PoseLandmark.RIGHT_ANKLE]
    left_shoulder = landmarks[PoseLandmark.LEFT_SHOULDER]
    right_shoulder = landmarks[PoseLandmark.RIGHT_SHOULDER]

    # =====================
    # 1. 초기 자세 기준으로 상체 수직 보정
    # =====================
    ideal_left_diff = initial_pose.get("left_shoulder_hip_diff")
    ideal_right_diff = initial_pose.get("right_shoulder_hip_diff")

    # 운동 자세 시작의 
    current_left_diff = left_shoulder['x'] - left_hip['x']
    current_right_diff = right_shoulder['x'] - right_hip['x']

    slope_threshold = 0.02  # 초기 기준 대비 허용 오차
    smooth_factor = 0.3     # 30%만 이동

    if ideal_left_diff is not None and abs(current_left_diff - ideal_left_diff) > slope_threshold:
        delta_x = (current_left_diff - ideal_left_diff) * smooth_factor
        landmarks[PoseLandmark.LEFT_SHOULDER]['x'] -= delta_x

    if ideal_right_diff is not None and abs(current_right_diff - ideal_right_diff) > slope_threshold:
        delta_x = (current_right_diff - ideal_right_diff) * smooth_factor
        landmarks[PoseLandmark.RIGHT_SHOULDER]['x'] -= delta_x

    # =====================
    # 2. 발 간격 거리 보정
    # =====================
    step_distance = abs(left_ankle['x'] - right_ankle['x'])
    minimum_step_distance = 0.2

    if step_distance < minimum_step_distance:
        expand_amount = (minimum_step_distance - step_distance) / 2
        landmarks[PoseLandmark.LEFT_ANKLE]['x'] += expand_amount
        landmarks[PoseLandmark.RIGHT_ANKLE]['x'] -= expand_amount

    # =====================
    # 3. 앞다리 무릎 각도 보정 (왼발)
    # =====================
    left_knee_angle = calculate_angle(left_hip, left_knee, left_ankle)

    if left_knee_angle < 80:
        landmarks[PoseLandmark.LEFT_KNEE]['y'] -= 0.02
    elif left_knee_angle > 100:
        landmarks[PoseLandmark.LEFT_KNEE]['y'] += 0.02

    # =====================
    # 4. 뒷다리 무릎 각도 보정 (오른발)
    # =====================
    right_knee_angle = calculate_angle(right_hip, right_knee, right_ankle)

    if right_knee_angle < 90:
        landmarks[PoseLandmark.RIGHT_KNEE]['y'] -= 0.02
    elif right_knee_angle > 120:
        landmarks[PoseLandmark.RIGHT_KNEE]['y'] += 0.02

    # =====================
    # 5. 골반 좌우 높이 맞추기
    # =====================
    pelvis_diff = abs(left_hip['y'] - right_hip['y'])
    pelvis_threshold = 0.02

    if pelvis_diff > pelvis_threshold:
        if left_hip['y'] > right_hip['y']:
            landmarks[PoseLandmark.LEFT_HIP]['y'] = right_hip['y']
        else:
            landmarks[PoseLandmark.RIGHT_HIP]['y'] = left_hip['y']

    # =====================
    # 6. 운동 과정 체크 (런지 내려가기-올라오기)
    # =====================
    current_hip_y = (left_hip['y'] + right_hip['y']) / 2
    back_knee_y = right_knee['y']

    bottom_threshold_knee_y = 0.9  # 최저점 y값 기준

    if previous_hip_y is None:
        previous_hip_y = current_hip_y
        min_hip_y = current_hip_y
        data["landmarks"] = landmarks
        data["lunge_count"] = completed_reps
        data["status"] = "standby"
        return data

    if current_hip_y > previous_hip_y + 0.005:
        is_descending = True
        min_hip_y = min(min_hip_y, current_hip_y)

    elif current_hip_y < previous_hip_y - 0.005:
        if is_descending and reached_bottom:
            completed_reps += 1
            is_descending = False
            reached_bottom = False
            print(f"✅ 런지 1회 완료! (총 {completed_reps}회)")

    if back_knee_y > bottom_threshold_knee_y:
        reached_bottom = True

    previous_hip_y = current_hip_y

    if is_descending:
        status = "down"
    else:
        status = "up"

    # =====================
    # 7. 최종 결과 반환
    # =====================
    data["landmarks"] = landmarks
    data["lunge_count"] = completed_reps
    data["status"] = status

    return data
