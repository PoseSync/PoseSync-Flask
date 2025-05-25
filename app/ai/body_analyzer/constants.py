"""개선된 체형 분석을 위한 상수값 정의 (연구 기반)"""

# 상완-전완 비율 임계값 (전완/상완 기준) - 빡빡한 기준
# 한국인 평균: 0.81±0.05 → 표준편차 범위를 좁혀서 민감하게 분류
ARM_RATIO_THRESHOLDS = {
    "LONG": [0.0, 0.79],      # 상완 발달형: 전완/상완 0.79 이하 (평균-0.02)
    "AVG": [0.80, 0.82],      # 평균형: 전완/상완 0.80 ~ 0.82 (±0.01 범위만)
    "SHORT": [0.83, 1.0]      # 전완 발달형: 전완/상완 0.83 이상 (평균+0.02)
}

# 상체-하체 비율 임계값 (하체/상체 기준) - 빡빡한 기준
# 평균 1.20 기준으로 ±0.05 범위만 AVG로 분류
UPPER_LOWER_RATIO_THRESHOLDS = {
    "UPPER": [1.26, 2.0],     # 상체 발달형: 하체/상체 1.26 이상
    "AVG": [1.15, 1.25],      # 평균형: 하체/상체 1.15 ~ 1.25 (좁은 범위)
    "LOWER": [0.0, 1.14]      # 하체 발달형: 하체/상체 1.14 이하
}

# 대퇴골-정강이 비율 임계값 (정강이/대퇴골 기준) - 빡빡한 기준
# 평균 0.87 기준으로 ±0.03 범위만 AVG로 분류
FEMUR_TIBIA_RATIO_THRESHOLDS = {
    "FEMUR": [0.0, 0.84],     # 대퇴골 발달형: 정강이/대퇴골 0.84 이하
    "AVG": [0.85, 0.89],      # 평균형: 정강이/대퇴골 0.85 ~ 0.89 (좁은 범위)
    "TIBIA": [0.90, 2.0]      # 정강이 발달형: 정강이/대퇴골 0.90 이상
}

# 고관절-신장 비율 임계값 - 빡빡한 기준
# 평균 19.5-20.5% 기준으로 좁은 범위만 AVG
HIP_HEIGHT_RATIO_THRESHOLDS = {
    "WIDE": [0.205, 0.30],    # 고관절 확장형: 0.205 이상
    "AVG": [0.190, 0.204],    # 평균형: 0.190 ~ 0.204 (좁은 범위)
    "NARROW": [0.0, 0.189]    # 고관절 슬림형: 0.189 이하
}

# 어깨-신장 비율 임계값 (추가)
# 남성 평균 23%, 여성 평균 21%
SHOULDER_HEIGHT_RATIO_THRESHOLDS = {
    "WIDE": [0.25, 0.35],     # 어깨 확장형: 0.25 이상
    "AVG": [0.20, 0.24],      # 평균형: 0.20 ~ 0.24
    "NARROW": [0.0, 0.19]     # 어깨 슬림형: 0.19 이하
}

# 체형 분류 결과 텍스트
BODY_TYPE_TEXT = {
    "arm": {
        "LONG": "상완 발달형",
        "AVG": "팔 비율 평균형",
        "SHORT": "전완 발달형"
    },
    "upper_lower": {
        "UPPER": "상체 발달형",
        "AVG": "상하체 비율 평균형",
        "LOWER": "하체 발달형"
    },
    "femur_tibia": {
        "FEMUR": "대퇴골 발달형",
        "AVG": "다리 비율 평균형",
        "TIBIA": "정강이 발달형"
    },
    "hip": {
        "WIDE": "고관절 확장형",
        "AVG": "고관절 너비 평균형",
        "NARROW": "고관절 슬림형"
    },
    "shoulder": {
        "WIDE": "어깨 확장형",
        "AVG": "어깨 너비 평균형",
        "NARROW": "어깨 슬림형"
    }
}

# 성별별 평균 비율 (참고용)
AVERAGE_RATIOS = {
    "male": {
        "forearm_to_upper_arm": 0.81,
        "lower_to_upper_body": 1.20,
        "tibia_to_femur": 0.87,
        "hip_to_height": 0.195,
        "shoulder_to_height": 0.23
    },
    "female": {
        "forearm_to_upper_arm": 0.81,
        "lower_to_upper_body": 1.20,
        "tibia_to_femur": 0.87,
        "hip_to_height": 0.205,
        "shoulder_to_height": 0.21
    }
}

# 측정 신뢰도 임계값
MEASUREMENT_RELIABILITY = {
    "min_confidence": 0.7,        # 최소 신뢰도
    "symmetry_threshold": 0.10,   # 좌우 대칭 허용 오차 (10%)
    "ratio_bounds": {             # 비율 유효성 검사
        "forearm_upper_arm": [0.5, 1.2],
        "tibia_femur": [0.6, 1.3],
        "lower_upper_body": [0.8, 1.8],
        "hip_height": [0.10, 0.35],
        "shoulder_height": [0.15, 0.35]
    }
}

# 연령별 보정 계수 (선택적 적용)
AGE_CORRECTION = {
    "child": (0, 12),      # 성장기
    "teen": (13, 19),      # 청소년기
    "adult": (20, 59),     # 성인
    "elderly": (60, 100)   # 고령
}