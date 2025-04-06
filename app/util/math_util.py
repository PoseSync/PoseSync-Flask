import numpy as np

# 벡터 정규화 함수
def normalize_vector(v):
    norm = np.linalg.norm(v)
    return v / norm if norm != 0 else v