import torch

# 파이토치 버전 출력
print(f"PyTorch version: {torch.__version__}")

# 파이토치가 사용 중인 CUDA 버전 출력
print(f"PyTorch CUDA version: {torch.version.cuda}")

# 현재 파이토치가 CUDA를 사용할 수 있는지 여부
print(f"Is CUDA available for PyTorch: {torch.cuda.is_available()}")

# 사용 가능한 GPU 개수
if torch.cuda.is_available():
    print(f"Number of GPUs available: {torch.cuda.device_count()}")
    # 현재 GPU 이름
    print(f"Current GPU name: {torch.cuda.get_device_name(0)}")