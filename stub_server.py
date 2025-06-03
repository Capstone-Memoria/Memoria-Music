import os
import asyncio
import uuid
import threading
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel

import logging
import json

# 로깅 설정
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# 설정값 및 상수
WORKING_DIR = os.path.dirname(os.path.abspath(__file__))
FINAL_MUSIC_DIR = os.path.join(WORKING_DIR, "stub_generated_music")

# 디렉토리 생성
os.makedirs(FINAL_MUSIC_DIR, exist_ok=True)

# 요청 큐 및 상태 관리
job_queue: Optional[asyncio.Queue] = None
active_job: Optional[str] = None
job_statuses: Dict[str, Dict] = {}
job_lock: Optional[asyncio.Lock] = None
job_update_event: Optional[asyncio.Event] = None
background_task: Optional[asyncio.Task] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 라이프사이클 관리"""
    global job_queue, job_lock, job_update_event, background_task

    # 시작 시 초기화
    logging.info("[스텁] 스텁 서버 시작 - 실제 음악 생성 없이 20초 후 완료 처리")
    job_queue = asyncio.Queue()
    job_lock = asyncio.Lock()
    job_update_event = asyncio.Event()

    # 백그라운드 태스크 시작
    background_task = asyncio.create_task(process_music_generation_queue())

    yield

    # 종료 시 정리
    if background_task and not background_task.done():
        background_task.cancel()
        try:
            await background_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="Yue 음악 생성 API (스텁 서버)",
    description="테스트용 스텁 서버 - 실제 음악 생성 없이 20초 후 완료 처리",
    version="1.0.0-stub",
    lifespan=lifespan
)

# CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MusicGenerationRequest(BaseModel):
    genre_txt: str
    lyrics_txt: str


class MusicGenerationResponse(BaseModel):
    job_id: str
    status: str


def create_empty_mp3_file(file_path: str):
    """빈 MP3 파일을 생성합니다 (최소한의 유효한 MP3 헤더 포함)"""
    # 최소한의 MP3 파일 헤더 (약 1초 길이의 무음)
    mp3_header = bytes([
        # MP3 헤더 시작
        0xFF, 0xFB, 0x90, 0x00,  # MP3 sync word와 헤더
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    ])

    with open(file_path, 'wb') as f:
        # 간단한 무음 MP3 데이터 생성 (약 1KB 크기)
        f.write(mp3_header)
        # 무음 데이터 추가
        f.write(b'\x00' * 1000)


async def process_music_generation_queue():
    """백그라운드에서 음악 생성 요청 큐를 처리하는 함수 (스텁 버전)"""
    global active_job

    while True:
        try:
            # 큐에서 작업 가져오기
            logging.info("음악 생성 큐에서 다음 작업을 기다리는 중...")
            job_id, genre_txt, lyrics_txt = await job_queue.get()
            logging.info(f"[스텁] 작업 시작: {job_id}")

            async with job_lock:
                active_job = job_id
                job_statuses[job_id]["status"] = "processing"
                job_update_event.set()
                logging.info(f"[스텁] 작업 상태 업데이트: {job_id} -> processing")

            try:
                # 스텁: 20초 대기
                logging.info(f"[스텁] 작업 {job_id}: 20초 대기 시작")
                await asyncio.sleep(600)

                # 빈 MP3 파일 생성
                final_file_name = f"{job_id}.mp3"
                final_file_path = os.path.join(
                    FINAL_MUSIC_DIR, final_file_name)
                create_empty_mp3_file(final_file_path)

                logging.info(
                    f"[스텁] 작업 {job_id}: 빈 MP3 파일 생성 완료 - {final_file_path}")

                # 작업 완료 상태 업데이트
                async with job_lock:
                    job_statuses[job_id]["status"] = "completed"
                    job_statuses[job_id]["file_path"] = final_file_path
                    job_statuses[job_id]["completed_at"] = datetime.now(
                    ).isoformat()
                    active_job = None
                    logging.info(f"[스텁] 작업 {job_id}: 상태 업데이트 -> completed")

                    # 이벤트 발생시켜 SSE 알림
                    job_update_event.set()

            except Exception as e:
                error_message = str(e)
                logging.error(
                    f"[스텁] 작업 {job_id}: 처리 중 예외 발생 - {error_message}")

                async with job_lock:
                    job_statuses[job_id]["status"] = "failed"
                    job_statuses[job_id]["error"] = error_message
                    job_statuses[job_id]["completed_at"] = datetime.now(
                    ).isoformat()
                    active_job = None
                    job_update_event.set()

            finally:
                # 작업 완료 표시
                job_queue.task_done()
                logging.info(f"[스텁] 작업 {job_id}: 큐 작업 완료 표시")

        except asyncio.CancelledError:
            logging.info("음악 생성 큐 처리가 취소되었습니다.")
            break
        except Exception as e:
            logging.error(f"큐 처리 중 예상치 못한 오류: {e}")
            await asyncio.sleep(1)  # 오류 시 잠시 대기


@app.post("/generate-music-async/", response_model=MusicGenerationResponse)
async def generate_music_async(request: MusicGenerationRequest):
    """
    장르와 가사 텍스트를 기반으로 음악을 비동기적으로 생성합니다. (스텁 버전)
    요청 ID를 즉시 반환하고 20초 후 완료 처리합니다.
    """
    # 고유 작업 ID 생성
    job_id = str(uuid.uuid4())

    logging.info(f"[스텁] 새 음악 생성 요청: {job_id}")
    logging.info(f"[스텁] 장르: {request.genre_txt[:50]}...")
    logging.info(f"[스텁] 가사: {request.lyrics_txt[:50]}...")

    # 작업 상태 추가
    async with job_lock:
        job_statuses[job_id] = {
            "status": "queued",
            "created_at": datetime.now().isoformat(),
            "completed_at": None,
            "file_path": None,
            "error": None
        }

    # 작업 큐에 추가
    await job_queue.put((job_id, request.genre_txt, request.lyrics_txt))

    # 작업 ID 반환
    return MusicGenerationResponse(job_id=job_id, status="queued")


@app.post("/generate-music-sync/")
async def generate_music_sync(request: MusicGenerationRequest):
    """
    장르와 가사 텍스트를 기반으로 음악을 동기적으로 생성합니다. (스텁 버전)
    20초 대기 후 빈 MP3 파일을 반환합니다.
    """
    logging.info("[스텁] 동기 음악 생성 요청")
    logging.info(f"[스텁] 장르: {request.genre_txt[:50]}...")
    logging.info(f"[스텁] 가사: {request.lyrics_txt[:50]}...")

    try:
        # 스텁: 60초 대기
        logging.info("[스텁] 60초 대기 시작")
        await asyncio.sleep(60)

        # 빈 MP3 파일 생성
        unique_id = str(uuid.uuid4())
        final_file_name = f"{unique_id}.mp3"
        final_file_path = os.path.join(FINAL_MUSIC_DIR, final_file_name)
        create_empty_mp3_file(final_file_path)

        logging.info(f"[스텁] 빈 MP3 파일 생성 완료: {final_file_path}")

        # 파일 응답 반환
        return FileResponse(
            path=final_file_path,
            filename=final_file_name,
            media_type="audio/mpeg"
        )

    except Exception as e:
        logging.error(f"[스텁] 동기 음악 생성 중 오류: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"음악 생성 중 오류 발생: {str(e)}")


@app.get("/job-status/{job_id}")
async def get_job_status(job_id: str):
    """특정 작업 ID의 상태를 반환합니다."""
    if job_id not in job_statuses:
        raise HTTPException(status_code=404, detail="해당 작업을 찾을 수 없습니다.")

    return job_statuses[job_id]


@app.get("/events")
async def sse_events():
    """SSE를 통해 음악 생성 작업 상태 업데이트를 스트리밍합니다."""
    async def event_generator():
        while True:
            # 이벤트 대기 또는 주기적인 신호 전송
            try:
                # 20초 타임아웃 설정
                await asyncio.wait_for(job_update_event.wait(), timeout=20.0)
            except asyncio.TimeoutError:
                # 타임아웃 발생 시 keep-alive 신호 전송
                yield {
                    "event": "keep_alive",
                    "data": "ping"
                }
                continue  # 다음 루프 실행

            # 현재 상태 정보
            async with job_lock:
                # 이벤트 초기화
                job_update_event.clear()

                # 모든 작업 상태 전송
                yield {
                    "event": "job_update",
                    "data": json.dumps({
                        "active_job": active_job,
                        "jobs": job_statuses
                    })
                }

            # 짧은 대기 시간 추가
            await asyncio.sleep(0.1)

    return EventSourceResponse(event_generator())


@app.get("/music/download/{job_id}")
async def download_music(job_id: str):
    """생성된 음악 파일을 다운로드합니다. (스텁 버전 - 빈 파일 반환)"""
    if job_id not in job_statuses:
        raise HTTPException(status_code=404, detail="해당 작업을 찾을 수 없습니다.")

    job_status = job_statuses[job_id]

    if job_status["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"다운로드할 수 없습니다. 현재 상태: {job_status['status']}"
        )

    file_path = job_status["file_path"]

    if not os.path.exists(file_path):
        # 파일이 없으면 새로 생성
        logging.info(f"[스텁] 파일이 없어서 새로 생성: {file_path}")
        create_empty_mp3_file(file_path)

    logging.info(f"[스텁] 빈 MP3 파일 다운로드: {job_id}")
    return FileResponse(
        path=file_path,
        filename=f"{job_id}.mp3",
        media_type="audio/mpeg"
    )


@app.get("/status")
def get_status():
    """현재 API 서버의 상태를 반환합니다."""
    return {
        "server_type": "stub",
        "active_job": active_job,
        "queue_size": job_queue.qsize() if job_queue and hasattr(job_queue, 'qsize') else "unknown",
        "job_count": len(job_statuses)
    }


@app.get("/jobs")
async def list_jobs():
    """모든 작업 목록을 반환합니다."""
    return job_statuses


@app.get("/")
async def root():
    """스텁 서버 루트 엔드포인트"""
    return {
        "message": "Yue 음악 생성 API 스텁 서버",
        "version": "1.0.0-stub",
        "description": "테스트용 서버 - 20초 후 빈 MP3 파일 생성"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8040, timeout_keep_alive=300)
