import pyrealsense2 as rs
import json
import time


def get_realsense_parameters():
    """실제 연결된 RealSense 카메라의 내부 파라미터를 가져옵니다."""
    try:
        # 카메라 파이프라인 설정
        pipeline = rs.pipeline()
        config = rs.config()
        config.enable_stream(rs.stream.color, 1920, 1080, rs.format.bgr8, 30)

        # 파이프라인 시작
        print("카메라에 연결 중...")
        profile = pipeline.start(config)
        print("카메라 연결 성공!")

        # 카메라 안정화를 위해 잠시 대기
        time.sleep(2)

        # 내부 파라미터 획득
        color_stream = profile.get_stream(rs.stream.color)
        color_intrinsics = color_stream.as_video_stream_profile().get_intrinsics()

        # 결과 출력
        result = {
            "width": color_intrinsics.width,
            "height": color_intrinsics.height,
            "fx": color_intrinsics.fx,
            "fy": color_intrinsics.fy,
            "cx": color_intrinsics.ppx,  # principal point x
            "cy": color_intrinsics.ppy,  # principal point y
            "distortion_model": str(color_intrinsics.model),
            "coeffs": list(color_intrinsics.coeffs)
        }

        # 파이프라인 종료
        pipeline.stop()

        return result

    except Exception as e:
        print(f"RealSense 카메라 파라미터 가져오기 실패: {e}")
        return None


# 파라미터 가져오기
camera_params = get_realsense_parameters()

if camera_params:
    print("\n카메라 내부 파라미터:")
    for key, value in camera_params.items():
        print(f"  {key}: {value}")

    # FOV 계산 (근사값)
    import math

    width = camera_params["width"]
    height = camera_params["height"]
    fx = camera_params["fx"]
    fy = camera_params["fy"]

    fov_h_rad = 2 * math.atan(width / (2 * fx))
    fov_v_rad = 2 * math.atan(height / (2 * fy))

    fov_h_deg = math.degrees(fov_h_rad)
    fov_v_deg = math.degrees(fov_v_rad)

    print(f"\n계산된 FOV: {fov_h_deg:.1f}° × {fov_v_deg:.1f}°")

    # 파이썬 코드 형식으로 출력 (하드코딩용)
    print("\n서버 코드에 삽입할 하드코딩 값:")
    print(f"""
# RealSense D415 카메라의 실제 측정된 파라미터 (해상도: {width}x{height})
camera_params = CameraParams(
    width={width},
    height={height},
    fx_px={fx},
    fy_px={fy},
    cx_px={camera_params["cx"]},
    cy_px={camera_params["cy"]}
)
""")

    # JSON 파일로 저장
    with open("camera_params.json", "w") as f:
        json.dump(camera_params, f, indent=4)
    print("\n파라미터를 camera_params.json 파일에 저장했습니다.")
else:
    print("카메라 연결에 실패했습니다.")


# FOV 값을 기반으로 파라미터 계산 (비교용)
def calculate_from_fov(width, height, fov_h_deg, fov_v_deg):
    fov_h_rad = math.radians(fov_h_deg)
    fov_v_rad = math.radians(fov_v_deg)

    fx = (width / 2) / math.tan(fov_h_rad / 2)
    fy = (height / 2) / math.tan(fov_v_rad / 2)

    return {
        "width": width,
        "height": height,
        "fx": fx,
        "fy": fy,
        "cx": width / 2,
        "cy": height / 2
    }


# 주어진 FOV 값으로 계산 (실제 카메라 해상도 사용)
fov_params = calculate_from_fov(1920, 1080, 64, 41)
print("\nFOV 64°×41°로 계산한 파라미터:")
for key, value in fov_params.items():
    if key in ["fx", "fy"]:
        print(f"  {key}: {value:.2f}")
    else:
        print(f"  {key}: {value}")

print("\nFOV 계산값을 사용한 하드코딩:")
print(f"""
# FOV 64°×41°로 계산한 파라미터 (해상도: 1280x720)
camera_params = CameraParams(
    width=1920,
    height=1080,
    fx_px={fov_params["fx"]:.2f},
    fy_px={fov_params["fy"]:.2f},
    cx_px={fov_params["cx"]},
    cy_px={fov_params["cy"]}
)
""")