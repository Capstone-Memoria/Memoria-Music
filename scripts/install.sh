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
mkdir -p m-a-p
cd m-a-p
git clone https://huggingface.co/m-a-p/YuE-s1-7B-anneal-en-cot

git clone https://huggingface.co/m-a-p/YuE-s2-1B-general

# 서버 프로젝트 클론
echo "Downloading server project..."
cd ..
git clone https://github.com/Capstone-Memoria/Memoria-Music.git
cd Memoria-Music
git switch quality

# 서버 프로젝트 설치
echo "Installing server project..."
pip install -r requirements-api.txt

