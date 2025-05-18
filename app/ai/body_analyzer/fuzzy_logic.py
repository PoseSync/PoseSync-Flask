import numpy as np

class FuzzyMembership:
    """퍼지 로직을 위한 멤버십 함수 모음"""
    
    @staticmethod
    def triangle(x, a, b, c):
        """삼각형 멤버십 함수
        a: 왼쪽 경계
        b: 중심점
        c: 오른쪽 경계
        """
        if x <= a or x >= c:
            return 0.0
        elif a < x <= b:
            return (x - a) / (b - a)
        else:  # b < x < c
            return (c - x) / (c - b)
    
    @staticmethod
    def trapezoid(x, a, b, c, d):
        """사다리꼴 멤버십 함수
        a: 왼쪽 하단 경계
        b: 왼쪽 상단 경계
        c: 오른쪽 상단 경계
        d: 오른쪽 하단 경계
        """
        if x <= a or x >= d:
            return 0.0
        elif a < x <= b:
            return (x - a) / (b - a)
        elif b < x <= c:
            return 1.0
        else:  # c < x < d
            return (d - x) / (d - c)
    
    @staticmethod
    def sigmoid(x, a, b):
        """시그모이드 멤버십 함수 
        a: 중간점
        b: 기울기 (양수면 증가, 음수면 감소)
        """
        return 1.0 / (1.0 + np.exp(-b * (x - a)))


class FuzzyLogic:
    """퍼지 로직 연산 처리"""
    
    @staticmethod
    def fuzzy_and(*args):
        """퍼지 AND 연산 (최소값)"""
        return min(args)
    
    @staticmethod
    def fuzzy_or(*args):
        """퍼지 OR 연산 (최대값)"""
        return max(args)
    
    @staticmethod
    def fuzzy_not(x):
        """퍼지 NOT 연산 (보수)"""
        return 1.0 - x
    
    @staticmethod
    def defuzzify_centroid(x_values, membership_values):
        """무게중심법을 이용한 비퍼지화"""
        if not any(membership_values):
            return 0.0
        
        return sum(x * m for x, m in zip(x_values, membership_values)) / sum(membership_values)
    
    @staticmethod
    def classify_with_fuzzy_rules(value, thresholds, categories):
        """퍼지 규칙을 이용한 분류
        value: 분류할 값
        thresholds: 카테고리별 임계값
        categories: 분류 카테고리 목록
        """
        memberships = {}
        
        for i, category in enumerate(categories):
            if i == 0:  # 첫 번째 카테고리 (예: SHORT)
                if value <= thresholds[category][0]:
                    memberships[category] = 1.0
                elif value < thresholds[category][1]:
                    memberships[category] = (thresholds[category][1] - value) / (thresholds[category][1] - thresholds[category][0])
                else:
                    memberships[category] = 0.0
            elif i == len(categories) - 1:  # 마지막 카테고리 (예: LONG)
                if value >= thresholds[category][1]:
                    memberships[category] = 1.0
                elif value > thresholds[category][0]:
                    memberships[category] = (value - thresholds[category][0]) / (thresholds[category][1] - thresholds[category][0])
                else:
                    memberships[category] = 0.0
            else:  # 중간 카테고리 (예: AVG)
                if thresholds[category][0] <= value <= thresholds[category][1]:
                    # 삼각형 멤버십 함수 적용
                    a = thresholds[category][0]
                    b = (thresholds[category][0] + thresholds[category][1]) / 2
                    c = thresholds[category][1]
                    memberships[category] = FuzzyMembership.triangle(value, a, b, c)
                else:
                    memberships[category] = 0.0
        
        # 최대 멤버십 값을 가진 카테고리 선택
        selected_category = max(memberships, key=memberships.get)
        confidence = memberships[selected_category]
        
        return selected_category, confidence