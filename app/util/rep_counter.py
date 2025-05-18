from collections import deque
from typing import List, Dict

class RepCounter:
    """
    ┌─ 사용 방법 ───────────────────────────────────────────────┐
    │ rc = RepCounter(anchor_id=PoseLandmark.LEFT_SHOULDER,    │
    │                  moving_id=PoseLandmark.LEFT_ELBOW,      │
    │                  axis='y',                               │
    │                  down_offset=0.12, up_offset=0.04)       │
    │ ... 매 프레임마다 ...                                    │
    │   completed = rc.update(landmarks)                       │
    │   if completed: send_count(rc.count)                     │
    └───────────────────────────────────────────────────────────┘
    """

    def __init__(self,
                 anchor_id: int,
                 moving_id: int,
                 axis: str = "y",
                 down_offset: float = 0.10,
                 up_offset: float = 0.03,
                 buffer_size: int = 3,
                 initial_state: str = "up") -> None:
        """
        anchor_id   : 기준 랜드마크 ID (예: 어깨)
        moving_id   : 움직이는 랜드마크 ID (예: 팔꿈치)
        axis        : 비교 축 ('x' | 'y' | 'z')
        down_offset : anchor 축 값보다 얼마나 내려가야 'down' 으로 간주할지
        up_offset   : anchor 축 값보다 얼마나 올라와야 'up' 으로 간주할지
        buffer_size : 이동 평균용 버퍼 크기
        initial_state: 시작 자세 ('up' 또는 'down')
        """
        self.anchor_id   = anchor_id
        self.moving_id   = moving_id
        self.axis        = axis
        self.down_offset = down_offset
        self.up_offset   = up_offset

        self.buffer      = deque(maxlen=buffer_size)
        self.state       = initial_state
        self.count       = 0

    def _value(self, lm: Dict[str, float]) -> float:
        return lm[self.axis]

    def update(self, landmarks: List[Dict[str, float]]) -> bool:
        """
        landmarks : MediaPipe 형식의 랜드마크 배열 (id 순서 보장)

        return    : 이번 프레임에서 **1회가 완료**됐으면 True
        """
        anchor_val = self._value(landmarks[self.anchor_id])
        moving_val = self._value(landmarks[self.moving_id])

        # 이동 평균으로 흔들림 최소화
        self.buffer.append(moving_val)
        smoothed = sum(self.buffer) / len(self.buffer)

        down_th = anchor_val - self.down_offset
        up_th   = anchor_val + self.up_offset

        completed = False
        if self.state == "up" and smoothed < down_th:
            self.state = "down"
        elif self.state == "down" and smoothed > up_th:
            self.state = "up"
            self.count += 1
            completed = True

        return completed

    # 보조 메서드
    def reset(self, initial_state: str = "up"):
        self.buffer.clear()
        self.state = initial_state
        self.count = 0 