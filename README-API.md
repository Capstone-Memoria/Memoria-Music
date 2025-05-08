# Memoria Music API 문서

## 개요

이 프로젝트는 Yue 음악 생성 Python 스크립트(`infer.py`)를 FastAPI를 사용하여 REST API로 노출합니다. 사용자는 API를 통해 장르와 가사 텍스트를 전달하여 음악(MP3 파일)을 생성하고 다운로드할 수 있습니다.

이제 동기식(Synchronous) 및 비동기식(Asynchronous) 요청 모두를 지원하며, SSE를 통한 실시간 작업 상태 알림 기능을 제공합니다.

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

서버는 기본적으로 `http://localhost:8080`에서 실행됩니다.

## API 엔드포인트

### 1. 비동기 음악 생성 API

```
POST /generate-music-async/
```

장르와 가사 텍스트를 기반으로 음악을 비동기적으로 생성합니다. 요청 ID를 즉시 반환하고 백그라운드에서 처리합니다.

**요청 본문 (Request Body)**: JSON 형식

```json
{
  "genre_txt": "신나는 K-POP",
  "lyrics_txt": "여름이 왔네 햇살이 빛나네\n바다로 가자 우리 함께"
}
```

**성공 응답 (HTTP 200 OK)**:

```json
{
  "job_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "queued"
}
```

### 2. 동기 음악 생성 API

```
POST /generate-music-sync/
```

장르와 가사 텍스트를 기반으로 음악을 동기적으로 생성하고 MP3 파일을 반환합니다.
이미 음악 생성 중이라면 429 오류를 반환합니다.

**요청 본문 (Request Body)**: JSON 형식

```json
{
  "genre_txt": "신나는 K-POP",
  "lyrics_txt": "여름이 왔네 햇살이 빛나네\n바다로 가자 우리 함께"
}
```

**성공 응답 (HTTP 200 OK)**:

- `Content-Type: audio/mpeg`
- 응답 본문(Body): 생성된 MP3 파일 데이터
- `Content-Disposition` 헤더를 통해 다운로드 파일명 지정 (`attachment; filename="<unique_id>.mp3"`)

**동시 요청 제한 응답 (HTTP 429 Too Many Requests)**:

```json
{
  "detail": "현재 다른 음악 생성 요청이 처리 중입니다. 잠시 후 다시 시도해주세요."
}
```

### 3. 작업 상태 확인 API

```
GET /job-status/{job_id}
```

특정 작업 ID의 상태를 반환합니다.

**응답 예시**:

```json
{
  "status": "completed", // "queued", "processing", "completed", "failed" 중 하나
  "created_at": "2023-11-20T15:30:45.123456",
  "completed_at": "2023-11-20T15:35:23.456789",
  "file_path": "/path/to/file.mp3",
  "error": null
}
```

### 4. 음악 다운로드 API

```
GET /music/download/{job_id}
```

생성된 음악 파일을 다운로드합니다. 작업이 완료된 경우만 다운로드 가능합니다.

**성공 응답 (HTTP 200 OK)**:

- `Content-Type: audio/mpeg`
- 응답 본문(Body): MP3 파일 데이터

**실패 응답 (HTTP 404 Not Found)**:

```json
{
  "detail": "해당 작업을 찾을 수 없습니다."
}
```

**작업 미완료 응답 (HTTP 400 Bad Request)**:

```json
{
  "detail": "다운로드할 수 없습니다. 현재 상태: processing"
}
```

### 5. 서버 상태 확인 API

```
GET /status
```

현재 API 서버의 상태를 반환합니다.

**응답 예시**:

```json
{
  "active_job": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "queue_size": 3,
  "job_count": 10
}
```

### 6. 작업 목록 확인 API

```
GET /jobs
```

모든 작업 목록과 상태를 반환합니다.

## SSE(Server-Sent Events) 이벤트 스트림

```
GET /events
```

SSE를 통해 음악 생성 작업 상태 업데이트를 실시간으로 전달받습니다.

**이벤트 형식**:

```
event: job_update
data: {
  "active_job": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "jobs": {
    "f47ac10b-58cc-4372-a567-0e02b2c3d479": {
      "status": "processing",
      "created_at": "2023-11-20T15:30:45.123456",
      "completed_at": null,
      "file_path": null,
      "error": null
    },
    "a1b2c3d4-e5f6-4321-b234-c56d7e8f9g0h": {
      "status": "completed",
      "created_at": "2023-11-20T15:25:12.123456",
      "completed_at": "2023-11-20T15:28:34.456789",
      "file_path": "/path/to/file.mp3",
      "error": null
    }
  }
}
```

## 클라이언트 사용 예제

### JavaScript (비동기 요청 및 SSE 사용)

```javascript
// 비동기 음악 생성 요청
async function generateMusicAsync(genreTxt, lyricsTxt) {
  const response = await fetch("/generate-music-async/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      genre_txt: genreTxt,
      lyrics_txt: lyricsTxt,
    }),
  });

  return await response.json();
}

// SSE 이벤트 수신
function listenForUpdates(onUpdate) {
  const eventSource = new EventSource("/events");

  eventSource.addEventListener("job_update", (event) => {
    const data = JSON.parse(event.data);
    onUpdate(data);
  });

  eventSource.onerror = (error) => {
    console.error("SSE 연결 오류:", error);
    eventSource.close();
    // 필요시 재연결 로직 구현
  };

  return eventSource;
}

// 음악 다운로드
function downloadMusic(jobId) {
  window.location.href = `/music/download/${jobId}`;
}

// 사용 예시
async function example() {
  // 1. 비동기 음악 생성 요청
  const result = await generateMusicAsync(
    "신나는 K-POP",
    "여름이 왔네 햇살이 빛나네\n바다로 가자 우리 함께"
  );
  console.log("작업 ID:", result.job_id);

  // 2. SSE로 상태 업데이트 수신
  const eventSource = listenForUpdates((data) => {
    console.log("업데이트:", data);

    // 내 작업이 완료되었는지 확인
    const myJob = data.jobs[result.job_id];
    if (myJob && myJob.status === "completed") {
      console.log("음악 생성 완료!");

      // 3. 음악 다운로드
      downloadMusic(result.job_id);

      // SSE 연결 종료
      eventSource.close();
    }
  });
}
```

### Python (상태 확인 후 다운로드)

```python
import requests
import time
import json

base_url = "http://localhost:8080"

# 비동기 음악 생성 요청
def request_music_generation(genre_txt, lyrics_txt):
    data = {
        "genre_txt": genre_txt,
        "lyrics_txt": lyrics_txt
    }

    response = requests.post(f"{base_url}/generate-music-async/", json=data)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"오류 발생: {response.text}")
        return None

# 작업 상태 확인
def check_job_status(job_id):
    response = requests.get(f"{base_url}/job-status/{job_id}")

    if response.status_code == 200:
        return response.json()
    else:
        print(f"상태 확인 오류: {response.text}")
        return None

# 음악 다운로드
def download_music(job_id, output_path):
    response = requests.get(f"{base_url}/music/download/{job_id}", stream=True)

    if response.status_code == 200:
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"음악 파일이 {output_path}에 저장되었습니다.")
        return True
    else:
        print(f"다운로드 오류: {response.text}")
        return False

# 사용 예시
def example():
    # 1. 비동기 음악 생성 요청
    result = request_music_generation(
        "신나는 K-POP",
        "여름이 왔네 햇살이 빛나네\n바다로 가자 우리 함께"
    )

    if not result:
        return

    job_id = result["job_id"]
    print(f"작업 ID: {job_id}")

    # 2. 작업 완료될 때까지 상태 확인
    while True:
        status = check_job_status(job_id)

        if not status:
            break

        print(f"현재 상태: {status['status']}")

        if status["status"] == "completed":
            # 3. 음악 다운로드
            download_music(job_id, f"generated_{job_id}.mp3")
            break
        elif status["status"] == "failed":
            print(f"음악 생성 실패: {status.get('error', '알 수 없는 오류')}")
            break

        # 5초 대기 후 다시 확인
        time.sleep(5)

if __name__ == "__main__":
    example()
```

## API 문서

API 서버가 실행 중일 때 다음 URL에서 자동 생성된 API 문서를 확인할 수 있습니다:

- Swagger UI: `http://localhost:8080/docs`
- ReDoc: `http://localhost:8080/redoc`
