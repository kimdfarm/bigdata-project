import requests
import gzip
import os
import orjson  # 🔥 기본 json보다 수배~수십배 빠른 고성능 JSON 파싱 라이브러리
from concurrent.futures import ThreadPoolExecutor
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import pandas as pd

# ==============================================================================
# 1. 전역 맵핑 및 환경 세팅
# ==============================================================================
TARGET_EVENTS = {
    "ForkEvent": "sampled_ForkEvent.csv",
    "IssuesEvent": "sampled_IssuesEvent.csv",
    "IssueCommentEvent": "sampled_IssueCommentEvent.csv",
    "PullRequestEvent": "sampled_PullRequestEvent.csv",
    "PullRequestReviewEvent": "sampled_PullRequestReviewEvent.csv",
    "PullRequestReviewCommentEvent": "sampled_PullRequestReviewCommentEvent.csv",
    "WatchEvent": "sampled_WatchEvent.csv"
}

current_dir = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(current_dir, "..", "data", "use")
os.makedirs(OUTPUT_DIR, exist_ok=True)

MAX_WORKERS = 4  # 네트워크 대역폭 및 CPU 코어 수에 맞게 조절 (8~16 추천)

def create_retry_session():
    session = requests.Session()
    retries = Retry(
        total=3,  # 타임아웃 방어를 위해 재시도 횟수 가볍게 조정
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retries, pool_connections=MAX_WORKERS, pool_maxsize=MAX_WORKERS)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

# 전역 세션 재사용으로 커넥션 풀링 극대화
GLOBAL_SESSION = create_retry_session()

# ==============================================================================
# 2. 단일 아워(Hour) 타깃 정밀 파싱 코어 로직 (스레드는 데이터 반환만 담당)
# ==============================================================================
def process_hour(year, month, day, hour):
    year_str = str(year)
    month_str = f"{int(month):02d}"
    day_str = f"{int(day):02d}"
    hour_str = f"{int(hour):02d}"
    
    url = f"https://data.gharchive.org/{year_str}-{month_str}-{day_str}-{hour}.json.gz"
    
    # 각 스레드가 독립적으로 데이터를 모을 로컬 버퍼
    local_buffers = {event_type: [] for event_type in TARGET_EVENTS.keys()}
    
    try:
        # 타임아웃을 현실적으로 세팅 (연결 10초, 수신 30초)
        response = GLOBAL_SESSION.get(url, stream=True, timeout=(300, 600))
        
        if response.status_code == 200:
            print(f"📥 수집 중: {year_str}-{month_str}-{day_str} {hour_str}시")
            with gzip.GzipFile(fileobj=response.raw) as f:
                for line in f:
                    try:
                        # 🔥 속도 혁신 1: json.loads 대신 orjson.loads 사용 (bytes 다이렉트 파싱)
                        event = orjson.loads(line)
                    except:
                        continue
                    
                    event_type = event.get("type")
                    if event_type not in TARGET_EVENTS:
                        continue
                        
                    actor_name = event.get('actor', {}).get('login', '').lower()
                    if 'bot' in actor_name or '[bot]' in actor_name:
                        continue
                    
                    raw_payload = event.get("payload", {})
                    refined_event = {
                        "id": event.get("id"),
                        "type": event_type,
                        "actor_login": event.get("actor", {}).get("login"),
                        "repo_name": event.get("repo", {}).get("name"),
                        "created_at": event.get("created_at"),
                    }

                    # 💡 이제 이벤트별로 1차원 평면 데이터만 추가합니다.
                    if event_type == "ForkEvent":
                        forkee = raw_payload.get("forkee", {})
                        refined_event.update({
                            "forkee_full_name": forkee.get("full_name"),
                            "stargazers_count": forkee.get("stargazers_count", 0),
                            "license_name": forkee.get("license", {}).get("name") if forkee.get("license") else None
                        })

                    elif event_type == "IssuesEvent":
                        issue = raw_payload.get("issue", {})
                        refined_event.update({
                            "action": raw_payload.get("action"),
                            "issue_title": issue.get("title"),
                            "issue_state": issue.get("state"),
                            "issue_comments": issue.get("comments", 0)
                        })

                    elif event_type == "IssueCommentEvent":
                        issue = raw_payload.get("issue", {})
                        comment = raw_payload.get("comment", {})
                        refined_event.update({
                            "action": raw_payload.get("action"),
                            "issue_title": issue.get("title"),
                            "comment_body": comment.get("body")
                        })

                    elif event_type == "PullRequestEvent":
                        # payload에서 pull_request 객체를 가져옵니다.
                        pr = raw_payload.get("pull_request", {})
                        
                        # head와 base는 nested 구조이므로 각각 분리해서 추출
                        head = pr.get("head", {})
                        base = pr.get("base", {})
                        
                        refined_event.update({
                            "action": raw_payload.get("action"),
                            "pr_number": pr.get("number"),
                            "pr_title": pr.get("title", "No Title"), # 제목이 없을 경우 대비
                            "pr_id": pr.get("id"),
                            "head_ref": head.get("ref"),              # 수정된 브랜치 이름
                            "base_ref": base.get("ref"),              # 타겟 브랜치 이름
                            "head_repo": head.get("repo", {}).get("name"), # 수정이 시작된 저장소
                            "base_repo": base.get("repo", {}).get("name"), # 합쳐질 저장소
                            "merged": pr.get("merged", False)
                        })

                    elif event_type == "PullRequestReviewCommentEvent":
                        comment = raw_payload.get("comment", {})
                        pr = raw_payload.get("pull_request", {})
                        user = comment.get("user", {})
                        
                        refined_event.update({
                            "action": raw_payload.get("action"),
                            "comment_id": comment.get("id"),
                            "pr_number": pr.get("number"),
                            "reviewer_login": user.get("login"),
                            "reviewer_type": user.get("type"), # Bot인지 사람인지 구별 가능!
                            "path": comment.get("path"),       # 지적받은 파일 경로
                            "body": comment.get("body"),       # 리뷰 상세 내용
                            "diff_hunk": comment.get("diff_hunk"), # 실제 지적된 코드 영역
                        })

                    elif event_type == "PullRequestReviewEvent":
                        review = raw_payload.get("review", {})
                        pr = raw_payload.get("pull_request", {})
                        user = review.get("user", {})
                        
                        refined_event.update({
                            "action": raw_payload.get("action"),             # 예: updated, submitted
                            "review_state": review.get("state"),             # 예: commented, approved, changes_requested
                            "reviewer_login": user.get("login"),             # 리뷰어 이름 (Copilot 등)
                            "reviewer_type": user.get("type"),               # Bot인지 User인지 구분
                            "pr_number": pr.get("number"),
                            "body": review.get("body", ""),                  # 리뷰 본문 (길이 분석 가능)
                            "submitted_at": review.get("submitted_at"),
                            "commit_id": review.get("commit_id")             # 리뷰 대상이 된 커밋
                        })
                    elif event_type == "WatchEvent":
                        refined_event.update({
                            "action": raw_payload.get("action"),
                            "repo_url": f"https://github.com/{event.get('repo', {}).get('name')}"
                        })

                    elif "Review" in event_type:
                        review = raw_payload.get("review", {})
                        pr = raw_payload.get("pull_request", {})
                        refined_event.update({
                            "review_state": review.get("state"),
                            "pr_title": pr.get("title")
                        })
                    local_buffers[event_type].append(refined_event)
                    
        elif response.status_code == 404:
            print(f"⚠️ 데이터 없음 (404): {year_str}-{month_str}-{day_str} {hour_str}시")
        else:
            print(f"❌ HTTP 에러 ({response.status_code}): {year_str}-{month_str}-{day_str} {hour_str}시")
            
    except Exception as e:
        print(f"💥 스레드 예외 발생 [{day_str}일 {hour_str}시]: {e}")
        
    return local_buffers  # 결과를 디스크에 쓰지 않고 메모리 객체로 통째로 반환!

# ==============================================================================
# 3. 마스터 함수 인터페이스 (최종 병합 및 원샷 디스크 쓰기 부임)
# ==============================================================================
def collect_github_data(year: int, month: int, start_day: int, end_day: int, selected_hours: list):
    print("="*60)
    print(f"🎯 GH Archive 초고속 병렬 데이터 수집 엔진 가동")
    print(f"📅 목표 기간: {year}년 {month:02d}월 {start_day:02d}일 ~ {end_day:02d}일")
    print(f"⏰ 타깃 시간대 범위: {sorted(selected_hours)}")
    print("="*60)
    
    tasks = []
    for day in range(start_day, end_day + 1):
        for hour in selected_hours:
            if 0 <= hour <= 23:
                tasks.append((year, month, day, hour))

    # 전역 마스터 버퍼 초기화
    master_buffers = {event_type: [] for event_type in TARGET_EVENTS.keys()}

    # 🔥 속도 혁신 3: 멀티스레드는 메모리 파싱만 수행하여 동시성 극대화
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = executor.map(lambda p: process_hour(*p), tasks)
        
        # 각 스레드가 가져온 결과 주머니를 마스터 주머니에 털어넣기
        for hour_buffer in results:
            for event_type, data_list in hour_buffer.items():
                if data_list:
                    master_buffers[event_type].extend(data_list)

    print("\n" + "="*60)
    print(f"💾 대용량 데이터 전처리 완료! 디스크 원샷 저장 시작...")
    print("="*60)

    # 🔥 속도 혁신 4: 락(Lock) 없이 마지막에 딱 한 번만 파일별로 I/O 수행
    for event_type, total_data in master_buffers.items():
        if total_data:
            file_name = TARGET_EVENTS[event_type]
            full_output_path = os.path.join(OUTPUT_DIR, file_name)
            df_new = pd.DataFrame(total_data)
            
            if not os.path.exists(full_output_path):
                df_new.to_csv(full_output_path, index=False, encoding='utf-8-sig')
            else:
                df_new.to_csv(full_output_path, mode='a', header=False, index=False, encoding='utf-8-sig')
            print(f"✅ {file_name} 저장 완료 ({len(total_data):,} 건 추가됨)")

    print("\n" + "="*60)
    print(f"🎉 모든 데이터 수집 및 파이프라인 컴파일 완료!")
    print("="*60)