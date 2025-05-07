# YuE 음악 생성 API 서버

YuE-exllamav2 프로젝트의 음악 생성 기능을 REST API로 제공하는 서버 애플리케이션입니다.

## 개요

이 API 서버는 YuE 음악 생성 모델을 기반으로 사용자가 제공한 장르와 가사 텍스트를 이용해 고품질의 음악을 생성하고 MP3 형식으로 제공합니다. FastAPI 프레임워크를 사용하여 구현되었으며, 동기적 방식으로 음악을 생성하고 다운로드할 수 있는 엔드포인트를 제공합니다.

## 기능

- 장르와 가사 텍스트 기반 음악 생성
- 생성된 음악 파일 다운로드
- API 상태 확인

## 기술 스택

- Python 3.8+
- FastAPI
- YuE-exllamav2 (음악 생성 모델)
- Uvicorn (ASGI 서버)

## 설치 방법

1. 의존성 패키지 설치:

```bash
# YuE 의존성 설치
pip install -r ../requirements.txt

# API 서버 의존성 설치
pip install -r requirements-api.txt
```

2. 모델 다운로드:
   - YuE-s1-7B-anneal-en-cot-exl2 (Stage 1 모델)
   - YuE-s2-1B-general-exl2 (Stage 2 모델)

## 실행 방법

```bash
python main.py
```

서버는 기본적으로 `http://localhost:8000`에서 실행됩니다.

## API 엔드포인트

### 1. 음악 생성 (동기 방식)

**엔드포인트**: `POST /generate-music-sync/`

**요청 본문**:

```json
{
  "genre_txt": "장르 설명 (예: K-pop upbeat energetic)",
  "lyrics_txt": "가사 내용"
}
```

**응답**: 생성된 MP3 파일

### 2. 음악 다운로드

**엔드포인트**: `GET /music/download/{file_id}`

**응답**: 요청한 MP3 파일

### 3. API 상태 확인

**엔드포인트**: `GET /status`

**응답**:

```json
{
  "is_generating_music": false,
  "available": true
}
```

## 동시 요청 처리

이 API는 리소스 집약적인 음악 생성 작업의 특성상 한 번에 하나의 요청만 처리할 수 있습니다. 이미 음악 생성 중인 상태에서 새로운 요청이 들어오면 HTTP 429 오류를 반환합니다.

## API 문서

API 서버가 실행 중일 때 다음 URL에서 자동 생성된 API 문서를 확인할 수 있습니다:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 사용 예시

### cURL을 사용한 음악 생성 요청

```bash
curl -X 'POST' \
  'http://localhost:8000/generate-music-sync/' \
  -H 'Content-Type: application/json' \
  -d '{
    "genre_txt": "K-pop upbeat energetic dance female bright vocal",
    "lyrics_txt": "[verse]\n너와 함께라면 모든 게 달라져\n세상이 아름답게 빛나고 있어\n\n[chorus]\n이 순간을 영원히 간직하고 싶어\n우리의 이야기는 계속될 거야"
  }' \
  --output generated_song.mp3
```

## 파일 구조

- `main.py`: API 서버 메인 애플리케이션
- `requirements-api.txt`: API 서버 의존성 패키지 목록
- `test_api.py`: API 테스트 스크립트
- `README.md`: 이 문서

## 라이선스

이 프로젝트는 원본 YuE-exllamav2 프로젝트의 라이선스를 따릅니다.
