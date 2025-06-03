#! /bin/bash

# git lfs 설치
echo "Installing git-lfs..."
curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | bash
apt install git-lfs -y
git lfs install

# requirements.txt 설치
pip install -r requirements.txt


# 서버 프로젝트로 이동
cd Memoria-Music

# 서버 프로젝트 설치
echo "Installing server project..."
pip install -r requirements-api.txt

# 서버 실행
echo "Starting server..."
./start.sh