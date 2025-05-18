import numpy as np
from .fuzzy_logic import FuzzyLogic, FuzzyMembership
from .constants import (
    ARM_RATIO_THRESHOLDS, 
    UPPER_LOWER_RATIO_THRESHOLDS, 
    FEMUR_TIBIA_RATIO_THRESHOLDS, 
    HIP_HEIGHT_RATIO_THRESHOLDS,
    BODY_TYPE_TEXT
)

class BodyAnalyzer:
    """체형 분석 AI 모델"""
    
    def __init__(self):
        """모델 초기화"""
        self.fuzzy_logic = FuzzyLogic()
    
    def calculate_body_ratios(self, landmarks, height_cm):
        """체형 관련 비율 계산"""
        # 키를 미터 단위로 변환
        height_m = height_cm / 100.0
        
        # 랜드마크 ID별 매핑
        lm_dict = {lm.get('id'): lm for lm in landmarks}
        
        # 랜드마크 추출
        left_shoulder = lm_dict.get(11)
        right_shoulder = lm_dict.get(12)
        left_elbow = lm_dict.get(13)
        right_elbow = lm_dict.get(14)
        left_wrist = lm_dict.get(15)
        right_wrist = lm_dict.get(16)
        left_hip = lm_dict.get(23)
        right_hip = lm_dict.get(24)
        left_knee = lm_dict.get(25)
        right_knee = lm_dict.get(26)
        left_ankle = lm_dict.get(27)
        right_ankle = lm_dict.get(28)
        
        # 거리 계산
        # 상완 길이 (어깨-팔꿈치)
        left_upper_arm_length = self._calculate_distance(left_shoulder, left_elbow)
        right_upper_arm_length = self._calculate_distance(right_shoulder, right_elbow)
        upper_arm_length = (left_upper_arm_length + right_upper_arm_length) / 2
        
        # 전완 길이 (팔꿈치-손목)
        left_forearm_length = self._calculate_distance(left_elbow, left_wrist)
        right_forearm_length = self._calculate_distance(right_elbow, right_wrist)
        forearm_length = (left_forearm_length + right_forearm_length) / 2
        
        # 상체 길이 (어깨-고관절)
        left_upper_body_length = self._calculate_distance(left_shoulder, left_hip)
        right_upper_body_length = self._calculate_distance(right_shoulder, right_hip)
        upper_body_length = (left_upper_body_length + right_upper_body_length) / 2
        
        # 대퇴골 길이 (고관절-무릎)
        left_femur_length = self._calculate_distance(left_hip, left_knee)
        right_femur_length = self._calculate_distance(right_hip, right_knee)
        femur_length = (left_femur_length + right_femur_length) / 2
        
        # 정강이 길이 (무릎-발목)
        left_tibia_length = self._calculate_distance(left_knee, left_ankle)
        right_tibia_length = self._calculate_distance(right_knee, right_ankle)
        tibia_length = (left_tibia_length + right_tibia_length) / 2
        
        # 하체 길이 (대퇴골 + 정강이)
        lower_body_length = femur_length + tibia_length
        
        # 고관절 너비 (왼쪽 고관절-오른쪽 고관절)
        hip_width = self._calculate_distance(left_hip, right_hip)
        
        # 비율 계산
        # 상완-전완 비율 (전완 / 상완)
        arm_ratio = forearm_length / upper_arm_length if upper_arm_length > 0 else 0
        
        # 상체-하체 비율 (하체 / 상체)
        upper_lower_ratio = lower_body_length / upper_body_length if upper_body_length > 0 else 0
        
        # 대퇴골-정강이 비율 (정강이 / 대퇴골)
        femur_tibia_ratio = tibia_length / femur_length if femur_length > 0 else 0
        
        # 고관절-신장 비율 (고관절 너비 / 신장)
        hip_height_ratio = hip_width / height_m if height_m > 0 else 0
        
        return {
            "arm_ratio": arm_ratio,
            "upper_lower_ratio": upper_lower_ratio,
            "femur_tibia_ratio": femur_tibia_ratio,
            "hip_height_ratio": hip_height_ratio,
            
            # 원시 측정값도 저장 (필요시)
            "raw_measurements": {
                "upper_arm_length": upper_arm_length,
                "forearm_length": forearm_length,
                "upper_body_length": upper_body_length,
                "femur_length": femur_length,
                "tibia_length": tibia_length,
                "hip_width": hip_width
            }
        }
    
    def classify_body_types(self, ratios):
        """체형 유형 분류 (퍼지 로직 적용)"""
        results = {}
        
        # 1. 상완-전완 비율 분류
        arm_type, arm_confidence = self.fuzzy_logic.classify_with_fuzzy_rules(
            ratios["arm_ratio"],
            ARM_RATIO_THRESHOLDS,
            ["LONG", "AVG", "SHORT"]
        )
        results["arm_type"] = {
            "type": arm_type,
            "confidence": arm_confidence,
            "ratio": f"1:{ratios['arm_ratio']:.2f}",
            "text": BODY_TYPE_TEXT["arm"][arm_type]
        }
        
        # 2. 상체-하체 비율 분류
        upper_lower_type, upper_lower_confidence = self.fuzzy_logic.classify_with_fuzzy_rules(
            ratios["upper_lower_ratio"],
            UPPER_LOWER_RATIO_THRESHOLDS,
            ["LOWER", "AVG", "UPPER"]
        )
        results["upper_lower_type"] = {
            "type": upper_lower_type,
            "confidence": upper_lower_confidence,
            "ratio": f"1:{ratios['upper_lower_ratio']:.2f}",
            "text": BODY_TYPE_TEXT["upper_lower"][upper_lower_type]
        }
        
        # 3. 대퇴골-정강이 비율 분류
        femur_tibia_type, femur_tibia_confidence = self.fuzzy_logic.classify_with_fuzzy_rules(
            ratios["femur_tibia_ratio"],
            FEMUR_TIBIA_RATIO_THRESHOLDS,
            ["FEMUR", "AVG", "TIBIA"]
        )
        results["femur_tibia_type"] = {
            "type": femur_tibia_type,
            "confidence": femur_tibia_confidence,
            "ratio": f"1:{ratios['femur_tibia_ratio']:.2f}",
            "text": BODY_TYPE_TEXT["femur_tibia"][femur_tibia_type]
        }
        
        # 4. 고관절-신장 비율 분류
        hip_type, hip_confidence = self.fuzzy_logic.classify_with_fuzzy_rules(
            ratios["hip_height_ratio"],
            HIP_HEIGHT_RATIO_THRESHOLDS,
            ["NARROW", "AVG", "WIDE"]
        )
        results["hip_type"] = {
            "type": hip_type,
            "confidence": hip_confidence,
            "ratio": f"{ratios['hip_height_ratio']:.2f}",
            "text": BODY_TYPE_TEXT["hip"][hip_type]
        }
        
        return results
    
    def _calculate_distance(self, point1, point2):
        """두 3D 점 사이의 유클리드 거리 계산"""
        if not point1 or not point2:
            return 0.0
            
        return np.sqrt(
            (point1['x'] - point2['x'])**2 +
            (point1['y'] - point2['y'])**2 +
            (point1['z'] - point2['z'])**2
        )
    
    def analyze(self, landmarks, height_cm):
        """체형 분석 메인 함수"""
        # 1. 체형 비율 계산
        ratios = self.calculate_body_ratios(landmarks, height_cm)
        
        # 2. 체형 유형 분류 (퍼지 로직 적용)
        classifications = self.classify_body_types(ratios)
        
        # 3. 앙상블 접근법: 여러 분류 결과를 종합하여 신뢰도 가중치 적용
        ensemble_result = self._apply_ensemble_weighting(classifications)
        
        # 4. 최종 결과 포맷팅
        result = {
            # 원본 분류 결과
            "classifications": classifications,
            
            # 앙상블 결과 (가중치 적용)
            "ensemble_result": ensemble_result,
            
            # 프론트엔드 표시용 요약
            "summary": {
                "arm_ratio": f"상완-전완 비율 | {classifications['arm_type']['ratio']} {classifications['arm_type']['text']}",
                "upper_lower_ratio": f"상체-하체 비율 | {classifications['upper_lower_type']['ratio']} {classifications['upper_lower_type']['text']}",
                "femur_tibia_ratio": f"대퇴골-정강이 비율 | {classifications['femur_tibia_type']['ratio']} {classifications['femur_tibia_type']['text']}",
                "hip_height_ratio": f"고관절-신장 비율 | {classifications['hip_type']['ratio']} {classifications['hip_type']['text']}"
            },
            
            # DB 저장용 타입
            "db_types": {
                "arm_type": classifications['arm_type']['type'],
                "upper_body_type": self._map_upper_lower_to_body_type(classifications['upper_lower_type']['type'], "upper"),
                "lower_body_type": self._map_upper_lower_to_body_type(classifications['upper_lower_type']['type'], "lower"),
                "femur_type": self._map_femur_tibia_to_femur_type(classifications['femur_tibia_type']['type']),
                "hip_wide_type": self._map_hip_to_wide_type(classifications['hip_type']['type']),
            }
        }
        
        return result
    
    def _apply_ensemble_weighting(self, classifications):
        """
        앙상블 가중치 적용 (신뢰도 기반)
        여러 분류 결과의 신뢰도를 고려하여 최종 결과 도출
        """
        # 각 카테고리별 가중치 정의 (중요도에 따라 조정 가능)
        category_weights = {
            "arm_type": 0.25,
            "upper_lower_type": 0.3,
            "femur_tibia_type": 0.25,
            "hip_type": 0.2
        }
        
        # 각 분류 결과의 신뢰도와 카테고리 가중치를 곱하여 신뢰 점수 계산
        confidence_scores = {}
        for category, result in classifications.items():
            confidence_scores[category] = result["confidence"] * category_weights[category]
        
        return {
            "confidence_scores": confidence_scores,
            "overall_confidence": sum(confidence_scores.values()) / sum(category_weights.values())
        }
    
    def _map_upper_lower_to_body_type(self, upper_lower_type, target):
        """상하체 비율 분류를 BodyType 모델 타입으로 변환"""
        if target == "upper":
            # 상체 타입 변환
            if upper_lower_type == "UPPER":
                return "LONG"
            elif upper_lower_type == "LOWER":
                return "SHORT"
            else:
                return "AVG"
        else:
            # 하체 타입 변환
            if upper_lower_type == "UPPER":
                return "SHORT"
            elif upper_lower_type == "LOWER":
                return "LONG"
            else:
                return "AVG"
    
    def _map_femur_tibia_to_femur_type(self, femur_tibia_type):
        """대퇴골-정강이 비율 분류를 대퇴골 타입으로 변환"""
        if femur_tibia_type == "FEMUR":
            return "LONG"
        elif femur_tibia_type == "TIBIA":
            return "SHORT"
        else:
            return "AVG"
    
    def _map_hip_to_wide_type(self, hip_type):
        """고관절 타입을 너비 타입으로 변환"""
        if hip_type == "WIDE":
            return "WIDE"
        elif hip_type == "NARROW":
            return "NARROW"
        else:
            return "AVG"