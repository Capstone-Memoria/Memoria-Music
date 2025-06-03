#!/bin/bash

# 디렉토리 경로 설정
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR="$( dirname "$DIR" )"

# PID 파일 경로 설정
PID_FILE="$ROOT_DIR/.server.pid"

# 이미 실행 중인지 확인
if [ -f "$PID_FILE" ]; then
  PID=$(cat "$PID_FILE")
  if ps -p $PID > /dev/null; then
    echo "서버가 이미 실행 중입니다. PID: $PID"
    exit 1
  else
    echo "이전에 비정상 종료된 서버 감지. PID 파일을 제거합니다."
    rm "$PID_FILE"
  fi
fi

# 서버 실행
echo "FastAPI 서버를 시작합니다..."
cd "$ROOT_DIR"
python main.py > "$ROOT_DIR/server.log" 2>&1 &

# PID 저장
PID=$!
echo $PID > "$PID_FILE"
echo "서버가 시작되었습니다. PID: $PID"
echo "로그는 server.log 파일에서 확인할 수 있습니다." 

# 로그 표시
tail -f "$ROOT_DIR/server.log"