import os
import sys
import pandas as pd
# 1. 현재 app.py 위치 계산
current_dir = os.path.dirname(os.path.abspath(__file__))

# 2. 💡 파이썬이 내부 모듈을 찾을 창고는 'src' 폴더로 지정합니다!
src_dir = os.path.join(current_dir, "src")

# 3. 그 'src' 폴더를 파이썬 최우선 검색 경로에 쾅 박아버립니다.
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# -------------------------------------------------------------
# 4. 이제 파이썬이 src 폴더 안을 뒤져서 에러 없이 쏙 가져옵니다.
import streamlit as st
from import_data import collect_github_data

st.set_page_config(
    page_title="GitHub Archive 동적 데이터 파이프라인",
    page_icon="🐙",
    layout="wide"
)

# 스마트 상대 경로 설정 (다른 PC 호환용)
base_path = os.path.join(current_dir, "data", "use")
os.makedirs(base_path, exist_ok=True)

st.title("🐙 GitHub Archive 빅데이터 분석 프로젝트")
st.markdown("---")

st.markdown("""
### 📊 프로젝트 개요
본 프로젝트는 **GitHub Archive 대용량 로그 데이터**를 기반으로 글로벌 오픈소스 생태계의 협업 환경을 분석하고 레포지토리 및 유저 랭킹을 도출하는 시스템입니다.

왼쪽 사이드바의 메뉴를 통해 단계별 분석 내용을 확인하실 수 있습니다:
* **📊 EDA**: 6가지 전체 이벤트별 데이터의 구조와 `payload` 내부의 가치 있는 상세 정보 탐색
* **📈 시각화**: 가중치 설정을 통한 글로벌 레포지토리 종합 랭킹 및 톱 유저 확인
* **🤖 모델 서비스**: 머신러닝(K-Means) 및 로컬 LLM(Ollama) 기반의 오픈소스 운영 환경 진단
""")

# ==============================================================================
# 🏎️ [최적화 핵심] 데이터 연산 캐싱 함수 (파일 내용이 안 바뀌면 초고속 RAM 반환)
# ==============================================================================
@st.cache_data(show_spinner=False)
def calculate_storage_status(folder_path, file_dict):
    """6개 파일의 건수와 시간 범위를 한 번에 고속 연산하고 캐싱하는 함수"""
    storage_timestamps = []
    file_status_list = []
    total_count = 0
    
    for event_name, file_name in file_dict.items():
        f_path = os.path.join(folder_path, file_name)
        if os.path.exists(f_path):
# 수정된 부분: usecols에 'created_at' 추가
            try:
                # 컬럼을 모두 불러와야 아래 코드에서 에러가 안 납니다.
                df_chk = pd.read_csv(f_path, usecols=['id', 'created_at']).dropna()
                count = len(df_chk)
                
                file_status_list.append({
                    "이벤트": event_name, 
                    "파일명": file_name, 
                    "수집 건수": f"{count:,} 건", 
                    "상태": "🟢 연동 중"
                })
                total_count += count
                
                if count > 0:
                    # 이제 'created_at'이 존재하므로 에러가 안 납니다.
                    storage_timestamps.extend(pd.to_datetime(df_chk['created_at']).tolist())
                    
            except Exception as e:
                # 오류 상세 내용을 보기 위해 print 추가
                print(f"Error processing {file_name}: {e}")
                file_status_list.append({"이벤트": event_name, "파일명": file_name, "수집 건수": "-", "상태": "🟡 파일 오류"})
        else:
            file_status_list.append({"이벤트": event_name, "파일명": file_name, "수집 건수": "0 건", "상태": "🔴 데이터 없음"})
            
    storage_time_text = ""
    if storage_timestamps:
        s_min = min(storage_timestamps).replace(minute=0, second=0, microsecond=0)
        if max(storage_timestamps).minute > 0 or max(storage_timestamps).second > 0:
            s_max = (max(storage_timestamps) + pd.Timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        else:
            s_max = max(storage_timestamps).replace(minute=0, second=0, microsecond=0)
        
        storage_time_text = f"{s_min.strftime('%Y-%m-%d %H:%M')} ~ {s_max.strftime('%Y-%m-%d %H:%M')}"
        
    return storage_time_text, file_status_list, total_count

# 고유 파일 명세 정의
files = {
    "ForkEvent": "sampled_ForkEvent.csv",
    "IssuesEvent": "sampled_IssuesEvent.csv",
    "IssueCommentEvent": "sampled_IssueCommentEvent.csv",
    "PullRequestEvent": "sampled_PullRequestEvent.csv",
    "PullRequestReviewEvent": "sampled_PullRequestReviewEvent.csv",
    "PullRequestReviewCommentEvent": "sampled_PullRequestReviewCommentEvent.csv",
    "WatchEvent": "sampled_WatchEvent.csv"
}

# 💡 상단/하단 연산 통합 유도 (여기서 딱 한 번만 캐시 데이터를 불러옵니다)
storage_time_text, file_status, total_rows = calculate_storage_status(base_path, files)
storage_has_data = True if total_rows > 0 else False

# ----------------- 🛠️ 데이터 수집 컨트롤러 UI 시작 -----------------
st.subheader("⚙️ 실시간 데이터 수집 및 정제 설정")
st.info("원하는 기간과 시간대를 선택하면 GH Archive 서버에서 데이터를 실시간으로 수집하여 전처리합니다.")

with st.expander("📂 수집 파라미터 설정 (시작/종료 시점 개별 지정)", expanded=True):
    
    col_start, col_end = st.columns(2)
    
    with col_start:
        st.markdown("#### 🟢 수집 시작 시점 설정")
        start_year = st.number_input("시작 연도", min_value=2015, max_value=2026, value=2026, key="s_year")
        start_month = st.selectbox("시작 월", list(range(1, 13)), index=4, key="s_month")
        start_day = st.number_input("시작 일", min_value=1, max_value=31, value=1, key="s_day")
        st.success(f"📌 **설정된 시작 시점:** {start_year}년 {start_month:02d}월 {start_day:02d}일")

    with col_end:
        st.markdown("#### 🔴 수집 종료 시점 설정")
        end_year = st.number_input("종료 연도", min_value=2015, max_value=2026, value=2026, key="e_year")
        end_month = st.selectbox("종료 월", list(range(1, 13)), index=4, key="e_month")
        end_day = st.number_input("종료 일", min_value=1, max_value=31, value=11, key="e_day")
        st.error(f"📌 **설정된 종료 시점:** {end_year}년 {end_month:02d}월 {end_day:02d}일")

    st.markdown("---")
    
    all_hours = list(range(24))
    target_hours = st.multiselect("⏰ 수집 시간대 선별 (Hour)", all_hours, default=[9], key="sel_hours")

    # 버튼 레이아웃 3분할 
    col_delete, col_btn1, col_btn2 = st.columns([1.5, 1, 1])
    
    # --- 🔴 1번 칸: 캐시 연동형 동적 데이터 삭제 버튼 구역 ---
    with col_delete:
        if not storage_has_data:
            st.button(
                "🛑 데이터가 존재하지 않으므로 누를 필요 없습니다.", 
                use_container_width=True, 
                disabled=True, 
                key="btn_empty_notice"
            )
        else:
            if st.button(
                f"🗑️ ({storage_time_text}) 데이터 삭제하기", 
                use_container_width=True, 
                type="primary", 
                key="btn_delete_storage"
            ):
                try:
                    for f in os.listdir(base_path):
                        if f.endswith(".csv"):
                            os.remove(os.path.join(base_path, f))
                    
                    # 💡 핵심 치트키 1: 파일 업로더 위젯의 세션 찌꺼기를 강제로 날려 화면에서 지웁니다.
                    if "demo_file_uploader" in st.session_state:
                        del st.session_state["demo_file_uploader"]
                    
                    # 💡 파일이 삭제되었으므로 캐시를 지워 대시보드 상태 갱신
                    st.cache_data.clear()
                    st.toast("💥 저장소의 모든 데이터가 깨끗하게 삭제되었습니다!")
                    st.rerun()
                except Exception as e:
                    st.error(f"삭제 중 오류 발생: {e}")
        
    # --- 🚀 2번 칸: 선택 조건으로 데이터 수집 시작 ---
    with col_btn1:
        if st.button("🚀 선택 조건으로 데이터 수집 시작", use_container_width=True, key="btn_collect_dynamic"):
            if (start_year > end_year) or (start_year == end_year and start_month > end_month) or (start_year == end_year and start_month == end_month and start_day > end_day):
                st.error("❌ 오류: 종료 시점이 시작 시점보다 빠릅니다! 기간 설정을 다시 확인해 주세요.")
            elif not target_hours:
                st.error("❌ 최소 하나 이상의 시간대를 선택해야 합니다.")
            else:
                start_txt = f"{start_year}년 {start_month:02d}월 {start_day:02d}일"
                end_txt = f"{end_year}년 {end_month:02d}월 {end_day:02d}일"
                
                with st.spinner(f"⏳ {start_txt} 부터 {end_txt} 까지의 대용량 데이터 추출 중..."):
                    try:
                        for f in os.listdir(base_path):
                            if f.endswith(".csv"):
                                os.remove(os.path.join(base_path, f))
                        
                        for yr in range(start_year, end_year + 1):
                            m_start = start_month if yr == start_year else 1
                            m_end = end_month if yr == end_year else 12
                            for mth in range(m_start, m_end + 1):
                                d_start = start_day if (yr == start_year and mth == start_month) else 1
                                d_end = end_day if (yr == end_year and mth == end_month) else 31
                                
                                collect_github_data(
                                    year=yr, month=mth, start_day=d_start, end_day=d_end, selected_hours=target_hours
                                )
                        
                        # 💡 신규 데이터 인젝션 완료 후 캐시 초기화 유도
                        st.cache_data.clear()
                        st.success(f"🎉 성공! 데이터가 정상적으로 저장됨!")
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        st.error(f"수집 파이프라인 가동 중 에러 발생: {e}")

    # --- ♻️ 3번 칸: 수동 데모 데이터 인젝션 ---
    with col_btn2:
    # 업로더 위젯 배치
        uploaded_demo_files = st.file_uploader(
            "클릭하여 데모 CSV 파일 선택", 
            type=["csv"], 
            accept_multiple_files=True, 
            key="demo_file_uploader",  # 💡 위에서 제어할 핵심 key
            label_visibility="collapsed"
        )
        st.caption("☝️ 위 구역 클릭 시 탐색기 팝업 (6개 CSV 선택)")

        # 파일이 새로 감지되었을 때만 주입 프로세스 가동
        if uploaded_demo_files:
            with st.spinner("📦 선택하신 데모 파일을 저장소에 저장하는 중..."):
                try:
                    # 1. 기존 폴더 안의 낡은 파일들 싹 청소
                    for f in os.listdir(base_path):
                        if f.endswith(".csv"):
                            os.remove(os.path.join(base_path, f))
                    
                    # 2. 새로운 파일들 안전하게 덮어쓰기
                    for file_obj in uploaded_demo_files:
                        with open(os.path.join(base_path, file_obj.name), "wb") as f:
                            f.write(file_obj.getbuffer())
                    
                    # 💡 핵심 치트키 2: 주입이 끝났으니 업로더 위젯의 파일 목록을 강제로 비워 리프레시 시 무한 루프를 막습니다.
                    del st.session_state["demo_file_uploader"]
                    
                    # 캐시 데이터 클리어하여 하단 상태창 갱신 유도
                    st.cache_data.clear()
                    st.toast("📂 데모 데이터가 정상 주입되었습니다.")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"💥 파일 저장 중 에러 발생: {e}")

# ==============================================================================
# 📊 3. UI 렌더링 마무리 구역 (중복 코드 완벽 제거 및 캐시 변수 다이렉트 출력)
# ==============================================================================
st.markdown("---")

if storage_time_text:
    usetitle = f"📅 현재 데이터 저장소 상태 기간 : {storage_time_text}"
else:
    usetitle = "📅 현재 데이터 저장소 상태 기간: 데이터가 존재하지 않습니다."

st.subheader(usetitle)

if total_rows > 0:
    st.table(pd.DataFrame(file_status))
    st.metric("총 분석 가능 로그 수", f"{total_rows:,} 개", help="캐싱 엔진이 연동된 실시간 누적 집계 데이터입니다.")
else:
    st.warning("분석할 데이터가 없습니다. 위의 설정창에서 데이터를 수집해 주세요.")