from tensorflow.keras.models import load_model

# 앱 시작 시 모델 한 번만 로드
fall_model = load_model("fall_detection_model.h5")