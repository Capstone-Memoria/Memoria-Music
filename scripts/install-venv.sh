#! /bin/bash

# 가상 환경 생성 및 활성화
echo "Creating and activating virtual environment..."
python -m venv venv
source venv/bin/activate

# 가상 환경에 pip 및 wheel 설치/업그레이드
echo "Installing/upgrading pip and wheel in virtual environment..."
pip install --upgrade pip wheel

# git lfs 설치
echo "Installing git-lfs..."
curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | bash
apt install git-lfs -y
git lfs install

# 프로젝트 다운로드
echo "Downloading project..."
git clone https://github.com/sgsdxzy/YuE-exllamav2
cd YuE-exllamav2
git clone https://huggingface.co/m-a-p/xcodec_mini_infer

# requirements.txt 설치 (가상 환경 내에서 실행)
echo "Installing requirements.txt..."
pip install -r requirements.txt

# 모델 다운로드
echo "Downloading models..."
mkdir -p Doctor-shotgun
cd Doctor-shotgun
git clone https://huggingface.co/Doctor-Shotgun/YuE-s1-7B-anneal-en-cot-exl2
cd YuE-s1-7B-anneal-en-cot-exl2
git switch 8.0bpw-h8

cd ..

git clone https://huggingface.co/Doctor-Shotgun/YuE-s2-1B-general-exl2
cd YuE-s2-1B-general-exl2
git switch 8.0bpw-h8

cd ..

# 서버 프로젝트 클론
echo "Downloading server project..."
cd ..
git clone https://github.com/Capstone-Memoria/Memoria-Music.git
cd Memoria-Music

# 서버 프로젝트 설치 (가상 환경 내에서 실행)
echo "Installing server project requirements..."
pip install -r requirements-api.txt

# 가상 환경 비활성화 (선택 사항)
# deactivate
