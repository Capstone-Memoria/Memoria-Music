# Yue 음악 생성 REST API

이 프로젝트는 Yue 음악 생성 Python 스크립트(`infer.py`)를 FastAPI를 사용하여 REST API로 노출합니다. 사용자는 API를 통해 장르와 가사 텍스트를 전달하여 음악(MP3 파일)을 생성하고 즉시 다운로드할 수 있습니다.

## 설치 방법

1. 기존 Yue 의존성 패키지 설치:

```bash
pip install -r requirements.txt
```

2. API 서버 의존성 패키지 설치:

```bash
pip install -r requirements-api.txt
```

## 실행 방법

다음 명령어로 API 서버를 실행합니다:

```bash
python main.py
```

서버는 기본적으로 `http://localhost:8000`에서 실행됩니다.

## API 엔드포인트

### 1. 음악 생성 (동기 방식)

**엔드포인트**: `POST /generate-music-sync/`

**요청 본문 (Request Body)**: JSON 형식

```json
{
  "genre_txt": "string (음악 장르 설명)",
  "lyrics_txt": "string (음악 가사 내용)"
}
```

**성공 응답 (HTTP 200 OK)**:

- `Content-Type: audio/mpeg`
- 응답 본문(Body): 생성된 MP3 파일 데이터
- `Content-Disposition` 헤더를 통해 다운로드 파일명 지정 (`attachment; filename="<unique_id>.mp3"`)

**실패 응답 (HTTP 500 Internal Server Error 또는 기타)**:

- `Content-Type: application/json`
- 응답 본문(Body):

```json
{
  "detail": "오류 메시지 (예: 음악 생성 스크립트 실패, 파일 처리 오류 등)"
}
```

**동시 요청 제한 응답 (HTTP 429 Too Many Requests)**:

- `Content-Type: application/json`
- 응답 본문(Body):

```json
{
  "detail": "현재 다른 음악 생성 요청이 처리 중입니다. 잠시 후 다시 시도해주세요."
}
```

### 2. 음악 다운로드

**엔드포인트**: `GET /music/download/{file_id}`

**경로 매개변수 (Path Parameter)**: `file_id` (MP3 파일의 고유 식별자, 확장자 제외. 예: UUID)

**성공 응답 (HTTP 200 OK)**:

- `Content-Type: audio/mpeg`
- 응답 본문(Body): `generated_music/{file_id}.mp3` 파일 데이터

**실패 응답 (HTTP 404 Not Found)**:

- `Content-Type: application/json`
- 응답 본문(Body):

```json
{
  "detail": "요청한 음악 파일을 찾을 수 없습니다."
}
```

### 3. API 상태 확인

**엔드포인트**: `GET /status`

**성공 응답 (HTTP 200 OK)**:

- `Content-Type: application/json`
- 응답 본문(Body):

```json
{
  "is_generating_music": boolean,  // 현재 음악 생성 중인지 여부
  "available": boolean             // API 사용 가능 여부
}
```

## 동시 요청 처리

이 API는 리소스 집약적인 음악 생성 작업의 특성상 한 번에 하나의 요청만 처리할 수 있도록 설계되었습니다. 이미 음악 생성 중인 상태에서 새로운 요청이 들어오면 HTTP 429 오류(Too Many Requests)를 반환합니다.

클라이언트는 `/status` 엔드포인트를 통해 API의 현재 상태를 확인하고, 사용 가능한 경우에만 요청을 보내는 것이 좋습니다.

## API 사용 예시

### cURL을 사용한 음악 생성 요청

```bash
# API 상태 확인
curl -X 'GET' 'http://localhost:8000/status'

# 음악 생성 요청
curl -X 'POST' \
  'http://localhost:8000/generate-music-sync/' \
  -H 'Content-Type: application/json' \
  -d '{
    "genre_txt": "K-pop upbeat energetic dance female bright vocal electronic inspiring",
    "lyrics_txt": "[verse]\n너와 함께라면 모든 게 달라져\n세상이 아름답게 빛나고 있어\n\n[chorus]\n이 순간을 영원히 간직하고 싶어\n우리의 이야기는 계속될 거야"
  }' \
  --output generated_song.mp3
```

### Python 요청 예시

```python
import requests
import time

base_url = "http://localhost:8000"

# API 상태 확인
def check_api_status():
    response = requests.get(f"{base_url}/status")
    if response.status_code == 200:
        return response.json()
    return {"available": False}

# 음악 생성 요청
def generate_music():
    data = {
        "genre_txt": "K-pop upbeat energetic dance female bright vocal electronic inspiring",
        "lyrics_txt": "[verse]\n너와 함께라면 모든 게 달라져\n세상이 아름답게 빛나고 있어\n\n[chorus]\n이 순간을 영원히 간직하고 싶어\n우리의 이야기는 계속될 거야"
    }

    # API 상태 확인
    status = check_api_status()
    if not status.get("available", False):
        print("API가 현재 사용 중입니다. 나중에 다시 시도하세요.")
        return False

    # 요청 전송
    response = requests.post(f"{base_url}/generate-music-sync/", json=data)

    if response.status_code == 200:
        # 파일 저장
        with open("generated_song.mp3", "wb") as f:
            f.write(response.content)
        print("음악 파일이 성공적으로 생성되었습니다.")
        return True
    elif response.status_code == 429:
        print("현재 다른 음악 생성 요청이 처리 중입니다. 잠시 후 다시 시도해주세요.")
        return False
    else:
        print(f"오류 발생: {response.json()['detail']}")
        return False

# 사용 예시
if __name__ == "__main__":
    generate_music()
```

## API 문서

API 서버가 실행 중일 때 다음 URL에서 자동 생성된 API 문서를 확인할 수 있습니다:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
