# app/util/pose_transform.py
"""
MediaPipe Pose 랜드마크 ↔ 사람-중심 좌표계 변환 유틸리티
- process_pose_landmarks()  : 월드 ➞ 사람-중심(-1~1) 정규화
- reverse_pose_landmarks()  : 정규화 ➞ 원본 월드 좌표
"""
from __future__ import annotations
from typing import List, Dict, Tuple, TypedDict
import numpy as np

Vec3 = Tuple[float, float, float]

class Landmark(TypedDict, total=False):
    id: int
    x : float
    y : float
    z : float
    visibility: float

class TransformData(TypedDict):
    maxValue : float
    hipCenter: Vec3
    axes     : Dict[str, Vec3]   # xAxis, yAxis, zAxis

# ──────────────────────────────────────────────────────────────────────────────
# 내부 수학 유틸
# ──────────────────────────────────────────────────────────────────────────────
def _normalize(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    return v if n == 0 else v / n

def _dot(a: Vec3, b: np.ndarray) -> float:
    return float(np.dot(np.array(a), b))

def _calculate_axes(lms: List[Landmark]) -> Dict[str, Vec3]:
    """
    xAxis: 왼어깨→오른어깨 (가로)
    yAxis: 양 힙-센터→양 어깨-센터 (세로)
    zAxis: xAxis × yAxis (카메라 기준 앞/뒤)
    """
    left_shoulder  = np.array([lms[11]['x'], lms[11]['y'], lms[11]['z']])
    right_shoulder = np.array([lms[12]['x'], lms[12]['y'], lms[12]['z']])
    left_hip       = np.array([lms[23]['x'], lms[23]['y'], lms[23]['z']])
    right_hip      = np.array([lms[24]['x'], lms[24]['y'], lms[24]['z']])

    shoulder_mid = 0.5 * (left_shoulder + right_shoulder)
    hip_mid      = 0.5 * (left_hip + right_hip)

    x_axis = _normalize(right_shoulder - left_shoulder)
    y_axis = _normalize(shoulder_mid - hip_mid)
    z_axis = _normalize(np.cross(x_axis, y_axis))       # 정직교화
    # y축을 재보정해 완전 직교 확보
    y_axis = _normalize(np.cross(z_axis, x_axis))

    return {
        "xAxis": tuple(x_axis),
        "yAxis": tuple(y_axis),
        "zAxis": tuple(z_axis)
    }

# ──────────────────────────────────────────────────────────────────────────────
# 정방향 변환
# ──────────────────────────────────────────────────────────────────────────────
def process_pose_landmarks(raw: List[Landmark]) -> Tuple[List[Landmark], TransformData]:

    print(f'정변환 전 => {raw}')

    """
    1) Hip-center 원점 이동
    2) 사람-중심 직교축 회전 (Rᵀ·v)
    3) -1~1 정규화 (공통 maxValue)
    반환: (정규화된 landmarks, transformData)
    """
    # hip 중심 산출
    left_hip  = raw[23]
    right_hip = raw[24]
    hip_center = (
        (left_hip['x'] + right_hip['x']) / 2,
        (left_hip['y'] + right_hip['y']) / 2,
        (left_hip['z'] + right_hip['z']) / 2
    )

    axes = _calculate_axes(raw)

    transformed: List[Landmark] = []
    max_val = 0.0

    for lm in raw:
        rel = np.array([
            lm['x'] - hip_center[0],
            lm['y'] - hip_center[1],
            lm['z'] - hip_center[2]
        ])
        local = np.array([
            _dot(axes['xAxis'], rel),
            _dot(axes['yAxis'], rel),
            _dot(axes['zAxis'], rel)
        ])
        max_val = max(max_val, np.abs(local).max())

        transformed.append({
            "id": lm['id'],
            "x": float(local[0]),
            "y": float(local[1]),
            "z": float(local[2]),
            "visibility": lm.get('visibility', 1.0)
        })

    # 공통 스케일 값으로 -1~1 매핑
    if max_val == 0:
        max_val = 1.0  # 안전장치

    for lm in transformed:
        lm['x'] /= max_val
        lm['y'] /= max_val
        lm['z'] /= max_val

    transform_data: TransformData = {
        "maxValue" : max_val,
        "hipCenter": hip_center,
        "axes"     : axes
    }


    return transformed, transform_data

# ──────────────────────────────────────────────────────────────────────────────
# 역방향 변환
# ──────────────────────────────────────────────────────────────────────────────
def reverse_pose_landmarks(
    norm: List[Landmark],
    td  : TransformData
) -> List[Landmark]:
    """
    td(maxValue, hipCenter, axes)를 사용해 원래 월드 좌표 재구성
    """
    axes = td['axes']
    max_v = td['maxValue']
    hc    = td['hipCenter']

    restored: List[Landmark] = []
    R = np.array([axes['xAxis'], axes['yAxis'], axes['zAxis']]).T  # 3×3

    for lm in norm:
        local = np.array([lm['x'] * max_v,
                          lm['y'] * max_v,
                          lm['z'] * max_v])
        world = R @ local + np.array(hc)

        restored.append({
            "id": lm['id'],
            "x" : float(world[0]),
            "y" : float(world[1]),
            "z" : float(world[2]),
            "visibility": lm.get('visibility', 1.0)
        })

    print(f'역변환 후 => {restored}')

    return restored
