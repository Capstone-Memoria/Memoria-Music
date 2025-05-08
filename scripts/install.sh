#! /bin/bash

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

# requirements.txt 설치
pip install -r requirements.txt

# 모델 다운로드
echo "Downloading models..."
mkdir -p Doctor-shotgun
cd Doctor-shotgun
git clone https://huggingface.co/Doctor-Shotgun/YuE-s1-7B-anneal-en-cot-exl2
cd YuE-s1-7B-anneal-en-cot-exl2
git switch 8.0bpw-h8

git clone https://huggingface.co/Doctor-Shotgun/YuE-s2-1B-general-exl2
cd YuE-s2-1B-general-exl2
git switch 8.0bpw-h8

