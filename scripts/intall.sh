#! /bin/bash

# 가상환경 설정
python -m venv venv
source venv/bin/activate

# git lfs 설치
git lfs install

# 프로젝트 다운로드
git clone https://github.com/sgsdxzy/YuE-exllamav2
cd YuE-exllamav2
git clone https://huggingface.co/m-a-p/xcodec_mini_infer
pip install -r requirements.txt

# 모델 다운로드
mkdir -p Doctor-shotgun
cd Doctor-shotgun
git clone https://huggingface.co/Doctor-Shotgun/YuE-s1-7B-anneal-en-cot-exl2
cd YuE-s1-7B-anneal-en-cot-exl2
git switch 8.0bpw-h8

git clone https://huggingface.co/Doctor-Shotgun/YuE-s2-1B-general-exl2
cd YuE-s2-1B-general-exl2
git switch 8.0bpw-h8

cd ../..


# API 서버 파일 다운로드
