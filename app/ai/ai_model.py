from tensorflow.keras.models import load_model
import numpy as np

# 앱 시작 시 모델 한 번만 로드
fall_model = load_model(r"c:\new_pose_sync\app\ai\fall_detection_model_v2.h5")
# retracing 방지를 위한 초기 더미 예측
fall_model.predict(np.zeros((1, 30, 6)))

# import os
# # 현재 파일(ai_model.py)이 있는 디렉토리 기준으로 상대 경로 생성
# current_dir = os.path.dirname(os.path.abspath(__file__))
# model_path = os.path.join(current_dir, "fall_detection_model_v2.h5")
# fall_model = load_model(model_path)