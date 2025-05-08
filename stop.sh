#!/bin/bash

# 디렉토리 경로 설정
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR="$( dirname "$DIR" )"

# PID 파일 경로 설정
PID_FILE="$ROOT_DIR/.server.pid"

# PID 파일이 존재하는지 확인
if [ ! -f "$PID_FILE" ]; then
  echo "서버가 실행 중이지 않습니다."
  exit 0
fi

# PID 파일 읽기
PID=$(cat "$PID_FILE")

# 프로세스 종료
if ps -p $PID > /dev/null; then
  echo "PID $PID 서버 종료 중..."
  kill $PID
  sleep 2
  
  # 프로세스가 계속 실행 중인지 확인
  if ps -p $PID > /dev/null; then
    echo "서버가 종료되지 않아 강제 종료합니다..."
    kill -9 $PID
  fi
  
  echo "서버가 종료되었습니다."
else
  echo "서버 프로세스($PID)가 이미 종료되었습니다."
fi

# PID 파일 삭제
rm "$PID_FILE" 