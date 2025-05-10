from tensorflow.keras.models import load_model
import numpy as np

# 앱 시작 시 모델 한 번만 로드
fall_model = load_model(r"c:\new_pose_sync\app\ai\fall_detection_model_v2.h5")
# retracing 방지를 위한 초기 더미 예측
fall_model.predict(np.zeros((1, 30, 6)))
