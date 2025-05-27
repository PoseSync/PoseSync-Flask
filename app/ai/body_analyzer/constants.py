"""개선된 체형 분석을 위한 상수값 정의 (연구 기반)"""

# 상완-전완 비율 임계값 (전완/상완 기준) - 빡빡한 기준
# 한국인 평균: 0.81±0.05 → 표준편차 범위를 좁혀서 민감하게 분류
ARM_RATIO_THRESHOLDS = {
    "LONG": [0.0000, 0.7999],      # 상완 발달형
    "AVG": [0.8000, 0.8299],       # 평균형
    "SHORT": [0.8300, 1.0000]      # 전완 발달형
}

UPPER_LOWER_RATIO_THRESHOLDS = {
    "LOWER": [0.0000, 1.1499],     # 하체 발달형
    "AVG": [1.1500, 1.2599],       # 평균형
    "UPPER": [1.2600, 2.0000]      # 상체 발달형
}

FEMUR_TIBIA_RATIO_THRESHOLDS = {
    "FEMUR": [0.0000, 0.8499],     # 대퇴골 발달형
    "AVG": [0.8500, 0.8999],       # 평균형
    "TIBIA": [0.9000, 2.0000]      # 정강이 발달형
}

HIP_HEIGHT_RATIO_THRESHOLDS = {
    "NARROW": [0.0000, 0.1899],    # 고관절 슬림형
    "AVG": [0.1900, 0.2049],       # 평균형
    "WIDE": [0.2050, 0.3000]       # 고관절 확장형
}

SHOULDER_HEIGHT_RATIO_THRESHOLDS = {
    "NARROW": [0.0000, 0.1999],    # 어깨 슬림형
    "AVG": [0.2000, 0.2499],       # 평균형
    "WIDE": [0.2500, 0.3500]       # 어깨 확장형
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