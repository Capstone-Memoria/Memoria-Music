import requests
import json
import os
import time

# API 엔드포인트 URL
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/generate-music-sync/"
STATUS_URL = f"{BASE_URL}/status"

# 테스트용 장르와 가사 데이터 (README.md 가이드라인에 맞게 수정)
test_data = {
    "genre_txt": "K-pop upbeat energetic dance female bright vocal electronic inspiring",
    "lyrics_txt": "[verse]\n너와 함께라면 모든 게 달라져\n세상이 아름답게 빛나고 있어\n\n[chorus]\n이 순간을 영원히 간직하고 싶어\n우리의 이야기는 계속될 거야"
}

def check_api_status():
    """API 서버의 상태를 확인합니다."""
    try:
        response = requests.get(STATUS_URL)
        if response.status_code == 200:
            return response.json()
        return {"available": False, "error": f"상태 확인 실패: {response.status_code}"}
    except Exception as e:
        return {"available": False, "error": f"상태 확인 중 오류: {str(e)}"}

def test_generate_music_sync():
    """음악 생성 API를 테스트합니다."""
    print("음악 생성 API 테스트 시작...")
    
    # API 상태 확인
    status = check_api_status()
    if not status.get("available", False):
        print(f"API를 사용할 수 없습니다: {status.get('error', '현재 음악 생성 중')}")
        return False
    
    try:
        # API 요청 전송
        response = requests.post(API_URL, json=test_data)
        
        # 응답 확인
        if response.status_code == 200:
            # 성공 시 MP3 파일 저장
            output_file = "test_generated_song.mp3"
            with open(output_file, "wb") as f:
                f.write(response.content)
            
            print(f"테스트 성공! 음악 파일이 '{output_file}'에 저장되었습니다.")
            print(f"파일 크기: {os.path.getsize(output_file) / 1024:.2f} KB")
            return True
        elif response.status_code == 429:
            # 이미 처리 중인 요청이 있는 경우
            print("현재 다른 음악 생성 요청이 처리 중입니다. 잠시 후 다시 시도해주세요.")
            return False
        else:
            # 기타 실패 시 오류 메시지 출력
            print(f"테스트 실패! 상태 코드: {response.status_code}")
            print(f"오류 메시지: {response.json()['detail']}")
            return False
    
    except Exception as e:
        print(f"테스트 중 예외 발생: {str(e)}")
        return False

def wait_and_retry(max_retries=3, wait_time=10):
    """API가 사용 가능해질 때까지 기다렸다가 요청을 재시도합니다."""
    for attempt in range(max_retries):
        status = check_api_status()
        if status.get("available", False):
            return test_generate_music_sync()
        
        print(f"API가 사용 중입니다. {wait_time}초 후 재시도합니다. (시도 {attempt+1}/{max_retries})")
        time.sleep(wait_time)
    
    print(f"{max_retries}번 시도 후에도 API를 사용할 수 없습니다.")
    return False

if __name__ == "__main__":
    # 기본 테스트 실행
    success = test_generate_music_sync()
    
    # 실패 시 재시도 여부 확인
    if not success:
        retry = input("API가 사용 중입니다. 사용 가능해질 때까지 기다렸다가 재시도하시겠습니까? (y/n): ")
        if retry.lower() == 'y':
            wait_and_retry() 