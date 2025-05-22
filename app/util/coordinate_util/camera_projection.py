# app/util/camera_projection.py
"""
MediaPipe landmarks를 화면 좌표계로 직접 투영하는 유틸리티
"""
from typing import List, Dict, Optional, Tuple


class CameraParams:
    """
    카메라 내부 파라미터를 관리하는 클래스
    """

    def __init__(
            self,
            width: int = 1280,
            height: int = 720,
            fx_px: float = 640.0,  # 픽셀 단위 초점 거리 X
            fy_px: float = 640.0,  # 픽셀 단위 초점 거리 Y
            cx_px: float = 640.0,  # 픽셀 단위 주점 X (일반적으로 중앙)
            cy_px: float = 360.0,  # 픽셀 단위 주점 Y
    ):
        self.width = width
        self.height = height
        self.fx_px = fx_px
        self.fy_px = fy_px
        self.cx_px = cx_px
        self.cy_px = cy_px

        # 정규화된 파라미터 (0~1 범위로 나타낸 값)
        self.fx = fx_px / width
        self.fy = fy_px / height
        self.cx = cx_px / width
        self.cy = cy_px / height

    @classmethod
    def from_realsense_d415(cls, width: int = 1280, height: int = 720):
        """
        Intel RealSense D415 카메라의 대략적인 기본 파라미터로 초기화
        """
        # 해상도에 맞게 스케일링된 값
        fx_px = 640.0 * (width / 1280.0)
        fy_px = 640.0 * (height / 720.0)
        cx_px = width / 2.0
        cy_px = height / 2.0

        return cls(width, height, fx_px, fy_px, cx_px, cy_px)


def project_landmarks_to_screen(
        landmarks: List[Dict[str, float]],
        camera_params: Optional[CameraParams] = None,
        cam_z: float = 1.5,  # 카메라-사용자 거리(미터)
        z_min: float = 0.5,  # 최소 깊이(미터)
        hip_center_2d: Optional[Tuple[float, float]] = None  # 실제 영상에서의 고관절 중심 좌표
) -> List[Dict[str, float]]:
    """
    MediaPipe landmarks를 화면 좌표계로 직접 투영
    실제 영상의 고관절 위치에 맞게 조정
    """
    if camera_params is None:
        camera_params = CameraParams(
            width=1920,
            height=1080,
            fx_px=1535.92,  # FOV 64° 기준
            fy_px=1344.15,  # FOV 41° 기준
            cx_px=960.0,
            cy_px=540.0
        )

    # 1. 모든 랜드마크를 투영
    projected = []
    for lm in landmarks:
        X, Y, Z = lm.get("x", 0.0), lm.get("y", 0.0), lm.get("z", 0.0)

        X_cam = -X
        Y_cam = Y

        depth = cam_z - Z
        if depth < z_min:
            depth = z_min

        x_screen_px = camera_params.fx_px * (X_cam / depth) + camera_params.cx_px
        y_screen_px = camera_params.fy_px * (Y_cam / depth) + camera_params.cy_px

        x_norm = x_screen_px / camera_params.width
        y_norm = y_screen_px / camera_params.height

        projected.append({
            "id": lm.get("id"),
            "x": x_norm,
            "y": y_norm,
            "z": Z,
            "visibility": lm.get("visibility", 1.0),
            "name": lm.get("name", "")
        })

    # 2. 실제 영상의 고관절 위치로 평행 이동
    if hip_center_2d is not None:
        # 투영된 고관절 중심 좌표 계산
        hip_ids = [23, 24]  # LEFT_HIP, RIGHT_HIP
        hip_landmarks = [lm for lm in projected if lm.get("id") in hip_ids]

        if len(hip_landmarks) >= 2:
            proj_hip_x = sum(lm["x"] for lm in hip_landmarks) / len(hip_landmarks)
            proj_hip_y = sum(lm["y"] for lm in hip_landmarks) / len(hip_landmarks)

            # 평행 이동 적용
            actual_hip_x, actual_hip_y = hip_center_2d
            offset_x = actual_hip_x - proj_hip_x
            offset_y = actual_hip_y - proj_hip_y

            print(f"투영된 고관절: ({proj_hip_x:.4f}, {proj_hip_y:.4f})")
            print(f"실제 고관절: ({actual_hip_x:.4f}, {actual_hip_y:.4f})")
            print(f"오프셋: ({offset_x:.4f}, {offset_y:.4f})")

            # 모든 랜드마크에 오프셋 적용
            for lm in projected:
                lm["x"] += offset_x
                lm["y"] += offset_y

    return projected