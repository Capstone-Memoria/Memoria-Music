import os
import subprocess
import tempfile
import uuid
import shutil
import threading
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel

# 설정값 및 상수
# 상위 디렉토리의 경로를 사용하도록 수정
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
YUE_INFER_SCRIPT = os.path.join(ROOT_DIR, "src", "yue", "infer.py")
# 메인 파일 기준 상위 디렉토리
WORKING_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(WORKING_DIR)
STAGE1_MODEL = "Doctor-shotgun/YuE-s1-7B-anneal-en-cot-exl2"
STAGE2_MODEL = "Doctor-Shotgun/YuE-s2-1B-general-exl2"
DEFAULT_OUTPUT_DIR = os.path.join(ROOT_DIR, "output")
DEFAULT_OUTPUT_FILENAME = "mixed.mp3"
FINAL_MUSIC_DIR = os.path.join(ROOT_DIR, "generated_music")

# 음악 생성 처리 상태를 추적하는 변수와 락
is_generating_music = False
generation_lock = threading.Lock()

# 디렉토리 생성
os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)
os.makedirs(FINAL_MUSIC_DIR, exist_ok=True)

app = FastAPI(
    title="Yue 음악 생성 API",
    description="장르와 가사 텍스트를 기반으로 음악을 생성하는 API",
    version="1.0.0"
)


class MusicGenerationRequest(BaseModel):
    genre_txt: str
    lyrics_txt: str


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
            # 장르와 가사를 임시 파일로 저장
            genre_file = tempfile.NamedTemporaryFile(
                mode='w+', suffix='.txt', delete=False)
            genre_file.write(request.genre_txt)
            genre_file.close()

            lyrics_file = tempfile.NamedTemporaryFile(
                mode='w+', suffix='.txt', delete=False)
            lyrics_file.write(request.lyrics_txt)
            lyrics_file.close()

            # infer.py 스크립트 실행 명령어 구성
            cmd = [
                "python",
                YUE_INFER_SCRIPT,
                "--stage1_use_exl2",
                "--stage2_use_exl2",
                "--stage2_cache_size", "32768",
                "--genre_txt", genre_file.name,
                "--lyrics_txt", lyrics_file.name,
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
            # 임시 파일 정리
            if genre_file and os.path.exists(genre_file.name):
                os.unlink(genre_file.name)
            if lyrics_file and os.path.exists(lyrics_file.name):
                os.unlink(lyrics_file.name)

    finally:
        # 처리 완료 후 상태 업데이트 및 락 해제
        is_generating_music = False
        generation_lock.release()


@app.get("/music/download/{file_id}")
def download_music(file_id: str):
    """
    생성된 음악 파일을 다운로드합니다.
    """
    file_path = os.path.join(FINAL_MUSIC_DIR, f"{file_id}.mp3")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="요청한 음악 파일을 찾을 수 없습니다.")

    return FileResponse(
        path=file_path,
        filename=f"{file_id}.mp3",
        media_type="audio/mpeg"
    )


@app.get("/status")
def get_status():
    """
    현재 API 서버의 상태를 반환합니다.
    """
    return {
        "is_generating_music": is_generating_music,
        "available": not is_generating_music
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, timeout_keep_alive=300)
