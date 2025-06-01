import os
import subprocess
import tempfile
import uuid
import shutil
import threading
import asyncio
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

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
# 상위 디렉토리의 경로를 사용하도록 수정
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
YUE_INFER_SCRIPT = os.path.join(ROOT_DIR, "src", "yue", "infer.py")
# 메인 파일 기준 상위 디렉토리
WORKING_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(WORKING_DIR)
STAGE1_MODEL = "m-a-p/YuE-s1-7B-anneal-jp-kr-cot"
STAGE2_MODEL = "m-a-p/YuE-s2-1B-general"
DEFAULT_OUTPUT_DIR = os.path.join(ROOT_DIR, "output")
DEFAULT_OUTPUT_FILENAME = "mixed.mp3"
FINAL_MUSIC_DIR = os.path.join(ROOT_DIR, "generated_music")

# 로컬 프롬프트 파일 경로
GENRE_FILE_PATH = os.path.join(ROOT_DIR, "input", "genre.txt")
LYRICS_FILE_PATH = os.path.join(ROOT_DIR, "input", "lyrics.txt")

# 음악 생성 처리 상태를 추적하는 변수와 락
is_generating_music = False
generation_lock = threading.Lock()

# 디렉토리 생성
os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)
os.makedirs(FINAL_MUSIC_DIR, exist_ok=True)
os.makedirs(os.path.join(ROOT_DIR, "input"), exist_ok=True)  # 입력 디렉토리 생성

# 요청 큐 및 상태 관리
job_queue = asyncio.Queue()
active_job: Optional[str] = None
job_statuses: Dict[str, Dict] = {}
job_lock = asyncio.Lock()
job_update_event = asyncio.Event()

app = FastAPI(
    title="Yue 음악 생성 API",
    description="장르와 가사 텍스트를 기반으로 음악을 생성하는 API",
    version="1.0.0"
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


async def process_music_generation_queue():
    """백그라운드에서 음악 생성 요청 큐를 처리하는 함수"""
    global active_job

    while True:
        # 큐에서 작업 가져오기
        logging.info("음악 생성 큐에서 다음 작업을 기다리는 중...")
        job_id, genre_txt, lyrics_txt = await job_queue.get()
        logging.info(f"작업 시작: {job_id}")

        async with job_lock:
            active_job = job_id
            job_statuses[job_id]["status"] = "processing"
            job_update_event.set()
            logging.info(f"작업 상태 업데이트: {job_id} -> processing")

        success = False
        result_file = None
        error_message = None

        try:
            # 로컬 파일에 장르와 가사 저장
            logging.info(f"작업 {job_id}: 장르 및 가사 파일 저장")
            with open(GENRE_FILE_PATH, "w", encoding="utf-8") as f:
                f.write(genre_txt)
            with open(LYRICS_FILE_PATH, "w", encoding="utf-8") as f:
                f.write(lyrics_txt)
            logging.info(f"작업 {job_id}: 장르 및 가사 파일 저장 완료")

            # infer.py 스크립트 실행
            cmd = [
                "python",
                YUE_INFER_SCRIPT,
                "--stage1_use_exl2",
                "--stage2_use_exl2",
                "--stage2_cache_size", "32768",
                "--genre_txt", GENRE_FILE_PATH,
                "--lyrics_txt", LYRICS_FILE_PATH,
                "--stage1_model", STAGE1_MODEL,
                "--stage2_model", STAGE2_MODEL
            ]

            logging.info(
                f"작업 {job_id}: infer.py 스크립트 실행 시작 - 명령어: {' '.join(cmd)}")
            # 비동기로 외부 프로세스 실행
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=PARENT_DIR
            )

            # 프로세스 대기
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_message = f"음악 생성 실패: {stderr.decode('utf-8')}"
                logging.error(f"작업 {job_id}: 스크립트 실행 오류 - {error_message}")
                raise Exception(error_message)

            logging.info(f"작업 {job_id}: infer.py 스크립트 실행 성공")
            # 생성된 MP3 파일 경로
            output_file_path = os.path.join(
                DEFAULT_OUTPUT_DIR, DEFAULT_OUTPUT_FILENAME)

            # 파일이 존재하는지 확인
            if not os.path.exists(output_file_path):
                error_message = "생성된 음악 파일을 찾을 수 없습니다."
                logging.error(f"작업 {job_id}: 출력 파일 없음 - {output_file_path}")
                raise Exception(error_message)

            logging.info(f"작업 {job_id}: 출력 파일 발견 - {output_file_path}")
            # 결과 파일 이름 생성 및 복사
            final_file_name = f"{job_id}.mp3"
            final_file_path = os.path.join(FINAL_MUSIC_DIR, final_file_name)
            shutil.copy2(output_file_path, final_file_path)
            logging.info(f"작업 {job_id}: 출력 파일 복사 완료 - {final_file_path}")

            success = True
            result_file = final_file_path

        except Exception as e:
            error_message = str(e)
            logging.error(f"작업 {job_id}: 처리 중 예외 발생 - {error_message}")

        finally:
            # 임시 파일 정리 로직 제거 (로컬 파일 사용)
            pass

            # 작업 완료 상태 업데이트
            async with job_lock:
                if success:
                    job_statuses[job_id]["status"] = "completed"
                    job_statuses[job_id]["file_path"] = result_file
                    logging.info(f"작업 {job_id}: 상태 업데이트 -> completed")
                else:
                    job_statuses[job_id]["status"] = "failed"
                    job_statuses[job_id]["error"] = error_message
                    logging.info(
                        f"작업 {job_id}: 상태 업데이트 -> failed - {error_message}")

                job_statuses[job_id]["completed_at"] = datetime.now(
                ).isoformat()
                active_job = None
                logging.info(f"작업 {job_id}: 처리 완료. active_job 초기화.")

                # 이벤트 발생시켜 SSE 알림
                job_update_event.set()

            # 작업 완료 표시
            job_queue.task_done()
            logging.info(f"작업 {job_id}: 큐 작업 완료 표시")


@app.on_event("startup")
async def startup_event():
    """서버 시작 시 백그라운드 태스크 시작"""
    asyncio.create_task(process_music_generation_queue())


@app.post("/generate-music-async/", response_model=MusicGenerationResponse)
async def generate_music_async(request: MusicGenerationRequest):
    """
    장르와 가사 텍스트를 기반으로 음악을 비동기적으로 생성합니다.
    요청 ID를 즉시 반환하고 백그라운드에서 처리합니다.
    """
    # 고유 작업 ID 생성
    job_id = str(uuid.uuid4())

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
def generate_music_sync(request: MusicGenerationRequest):
    """
    장르와 가사 텍스트를 기반으로 음악을 동기적으로 생성하고 MP3 파일을 반환합니다.
    이미 음악 생성 중이라면 429 오류를 반환합니다.
    """
    global is_generating_music

    # 현재 음악 생성 중인지 확인
    if not generation_lock.acquire(blocking=False):
        raise HTTPException(
            status_code=429,
            detail="현재 다른 음악 생성 요청이 처리 중입니다. 잠시 후 다시 시도해주세요."
        )

    try:
        is_generating_music = True

        # 임시 파일 생성
        genre_file = None
        lyrics_file = None

        try:
            # 장르와 가사를 로컬 파일로 저장
            with open(GENRE_FILE_PATH, "w", encoding="utf-8") as f:
                f.write(request.genre_txt)
            with open(LYRICS_FILE_PATH, "w", encoding="utf-8") as f:
                f.write(request.lyrics_txt)

            # infer.py 스크립트 실행 명령어 구성
            cmd = [
                "python",
                YUE_INFER_SCRIPT,
                "--stage1_use_exl2",
                "--stage2_use_exl2",
                "--stage2_cache_size", "32768",
                "--genre_txt", GENRE_FILE_PATH,  # 로컬 파일 경로 사용
                "--lyrics_txt", LYRICS_FILE_PATH,  # 로컬 파일 경로 사용
                "--stage1_model", STAGE1_MODEL,
                "--stage2_model", STAGE2_MODEL
            ]

            # 스크립트 실행
            result = subprocess.run(
                cmd,
                stdout=None,
                stderr=None,
                text=True,
                check=False,
                cwd=PARENT_DIR  # main.py 기준 상위 디렉토리를 작업 디렉토리로 설정
            )

            # 실행 결과 확인
            if result.returncode != 0:
                error_msg = "음악 생성 실패: 콘솔 출력을 확인해주세요."
                raise HTTPException(status_code=500, detail=error_msg)

            # 생성된 MP3 파일 경로
            output_file_path = os.path.join(
                DEFAULT_OUTPUT_DIR, DEFAULT_OUTPUT_FILENAME)

            # 파일이 존재하는지 확인
            if not os.path.exists(output_file_path):
                raise HTTPException(
                    status_code=500, detail="생성된 음악 파일을 찾을 수 없습니다.")

            # 고유 ID 생성
            unique_id = str(uuid.uuid4())
            final_file_name = f"{unique_id}.mp3"
            final_file_path = os.path.join(FINAL_MUSIC_DIR, final_file_name)

            # 파일 이동
            shutil.copy2(output_file_path, final_file_path)

            # 파일 응답 반환
            return FileResponse(
                path=final_file_path,
                filename=final_file_name,
                media_type="audio/mpeg"
            )

        except Exception as e:
            # 예외 처리
            raise HTTPException(
                status_code=500, detail=f"음악 생성 중 오류 발생: {str(e)}")

        finally:
            # 임시 파일 정리 로직 제거 (로컬 파일 사용)
            pass

    finally:
        # 처리 완료 후 상태 업데이트 및 락 해제
        is_generating_music = False
        generation_lock.release()


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
    """생성된 음악 파일을 다운로드합니다."""
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
        raise HTTPException(status_code=404, detail="음악 파일을 찾을 수 없습니다.")

    return FileResponse(
        path=file_path,
        filename=f"{job_id}.mp3",
        media_type="audio/mpeg"
    )


@app.get("/status")
def get_status():
    """현재 API 서버의 상태를 반환합니다."""
    return {
        "active_job": active_job,
        "queue_size": job_queue.qsize() if hasattr(job_queue, 'qsize') else "unknown",
        "job_count": len(job_statuses)
    }


@app.get("/jobs")
async def list_jobs():
    """모든 작업 목록을 반환합니다."""
    return job_statuses


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, timeout_keep_alive=300)
