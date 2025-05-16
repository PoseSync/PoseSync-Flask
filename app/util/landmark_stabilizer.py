class DeadZoneStabilizer:
    def __init__(self, dead_zone=0.01):
        """
        데드존만 사용하는 단순한 안정화기

        dead_zone: 움직임을 무시할 임계값 (기본값: 0.01)
        """
        self.dead_zone = dead_zone
        self.prev_landmarks = {}  # 이전 랜드마크 위치

    def apply_dead_zone(self, new_value, old_value):
        """
        데드존 적용: 변화량이 임계값보다 작으면 이전 값 유지
        """
        if abs(new_value - old_value) < self.dead_zone:
            return old_value  # 변화가 작으면 이전 값 유지
        return new_value  # 변화가 크면 새 값 사용

    def stabilize_landmarks(self, landmarks, dead_zone=None):
        """
        랜드마크 배열에 데드존 필터 적용

        landmarks: 랜드마크 배열
        dead_zone: 기본값 대신 사용할 데드존 (선택사항)

        returns: 안정화된 랜드마크 배열
        """
        if not landmarks or len(landmarks) == 0:
            return landmarks

        # 호출 시 데드존 값이 지정되면 그 값 사용
        current_dead_zone = dead_zone if dead_zone is not None else self.dead_zone

        stabilized_landmarks = []

        for i, landmark in enumerate(landmarks):
            # ID가 있으면 사용, 없으면 인덱스를 ID로 사용
            landmark_id = landmark.get('id', i)

            # 이전 위치 가져오기 (없으면 현재 위치)
            prev_landmark = self.prev_landmarks.get(landmark_id, landmark)

            # 데드존 적용
            stabilized = landmark.copy()  # 원본 복사

            # x 좌표에 데드존 적용
            stabilized['x'] = self.apply_dead_zone(
                landmark['x'],
                prev_landmark.get('x', landmark['x'])
            )

            # y 좌표에 데드존 적용
            stabilized['y'] = self.apply_dead_zone(
                landmark['y'],
                prev_landmark.get('y', landmark['y'])
            )

            # z 좌표가 있으면 데드존 적용
            if 'z' in landmark:
                stabilized['z'] = self.apply_dead_zone(
                    landmark['z'],
                    prev_landmark.get('z', landmark['z'])
                )

            stabilized_landmarks.append(stabilized)

            # 다음 프레임을 위해 현재 위치 저장
            self.prev_landmarks[landmark_id] = stabilized

        return stabilized_landmarks

    def set_dead_zone(self, dead_zone):
        """
        데드존 값 업데이트
        """
        self.dead_zone = dead_zone

    def reset(self):
        """
        이전 위치 기록 초기화
        """
        self.prev_landmarks.clear()


# 싱글톤 인스턴스 생성
landmark_stabilizer = DeadZoneStabilizer(dead_zone=0.02)  # 데드존 값 설정