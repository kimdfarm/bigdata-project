import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

import os

from src.data_loader import load_processed_data , save_all_results
from src.features import apply_use , load_data_from_disk
import json
data = None

# 1. 전역 모델 변수 선언 (아직 모델을 로드하지 않은 상태)

# --- 1. 데이터 로드 및 전처리 ---
SAVE_DIR = "bigdata_presentation/project_template/data/model"



@st.cache_data
def get_clustered_data(_progress_bar, _status_text , reviewer_filter = "User만 포함"):
    df_issue, df_pr, df_fork, df_issue_comment, df_issues, df_pr_comment, df_pr_review = load_processed_data()
    if reviewer_filter == "User만 포함":
            # 1) 리뷰어 타입 필터링 (기존)
        if 'reviewer_type' in df_pr_review.columns:
            df_pr_review = df_pr_review[df_pr_review['reviewer_type'] == 'User']
        
        # 2) Pull Request 생성자 필터링 추가 (추천!)
        if 'reviewer_type' in df_pr.columns:
            df_pr = df_pr[df_pr['reviewer_type'] == 'User']
            
        # 3) PR 코멘트 필터링 추가 (추천!)
        if 'reviewer_type' in df_pr_comment.columns:
            df_pr_comment = df_pr_comment[df_pr_comment['reviewer_type'] == 'User']

    df_issue_comment['event_type'] = 'IssueCommentEvent'
    df_issues['event_type'] = 'IssuesEvent'
    df_pr_comment['event_type'] = 'PullRequestReviewCommentEvent'
    df_pr_review['event_type'] = 'PullRequestReviewEvent'
    

    df_issue, issue_labels = apply_use(df_issue)
    df_pr, pr_labels = apply_use(df_pr)
    return df_issue, df_pr, df_fork, issue_labels, pr_labels ,  df_issue_comment, df_issues, df_pr_comment, df_pr_review

# [1] 설정은 오직 한 번만, 최상단에!
st.set_page_config(layout="wide")

# [2] 초기화
os.makedirs(SAVE_DIR, exist_ok=True)



# 데이터를 저장할 세션 스테이트 설정
if 'data' not in st.session_state:
    st.session_state['data'] = None

# [3] 사이드바 관리
st.title("🛠️ 데이터 및 모델 관리")
col1, col2, col3 = st.columns(3)

# 🗑️ 삭제 로직
with col1:
    # 1. 현재 폴더 상태 확인
    files = [f for f in os.listdir(SAVE_DIR) if os.path.isfile(os.path.join(SAVE_DIR, f))]
    file_count = len(files)
    
    # 2. 상태 알림 (정보 표시)
    if file_count > 0:
        st.warning(f"현재 데이터 파일 {file_count}개가 저장되어 있습니다.")
        with st.expander("파일 목록 보기"):
            st.write(files)
    else:
        st.info("현재 저장된 데이터 파일이 없습니다.")
    
    # 3. 삭제 버튼
    if st.button("🗑️ 모든 데이터 삭제"):
        if file_count > 0:
            for filename in files:
                os.remove(os.path.join(SAVE_DIR, filename))
            st.session_state['data'] = None
            st.success("모든 데이터가 삭제되었습니다.")
            st.rerun() # 즉시 화면 갱신
        else:
            st.info("삭제할 파일이 없습니다.")

# 🚀 학습 로직
with col2:
    reviewer_mode = st.radio("리뷰어 모드:", ["User만 포함", "User 및 Bot 포함"])
    if st.button("🚀 학습"):
        # 1. 학습 상태를 보여줄 컨테이너 생성
        status_container = st.sidebar.container()
        
        with status_container:
            st.info("모델 학습을 시작합니다.")
            empty = st.empty()
            empty2 = st.empty()
            empty3 = st.empty()
            empty4 = st.empty()
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # 2. 실제 학습 수행 (진행률 UI 객체 전달)
            # get_clustered_data 내부에서 progress_bar와 status_text를 업데이트하도록 구현해야 합니다.
            data = get_clustered_data(progress_bar, status_text, reviewer_filter=reviewer_mode)
            
            # 3. 결과 저장
            save_all_results(data , SAVE_DIR)
            
            # 4. 세션 저장 및 화면 갱신
            st.session_state['data'] = data
            progress_bar.empty()
            status_text.empty()
            st.success("✅ 학습 및 저장 완료!")
            st.rerun() # 전체 페이지를 새로고침하여 로드된 데이터로 UI 구성

# 📂 로드 로직
with col3:
    if st.button("로드"):
        loaded_data = load_data_from_disk(SAVE_DIR=SAVE_DIR) 
        if loaded_data:
            st.session_state['loaded_data'] = loaded_data
            st.success("데이터가 성공적으로 로드되었습니다!")
            # 3. 데이터가 들어왔으니 강제 새로고침 혹은 메시지 갱신
            st.rerun()
        else:
            uploaded_files = st.sidebar.file_uploader(
                "클릭하여 데이터 파일 선택", 
                type=["parquet", "json", "csv"], 
                accept_multiple_files=True, 
                key="demo_file_uploader"
            )
            st.sidebar.caption("☝️ 위 구역 클릭 시 탐색기 팝업 (필요한 파일 전체 선택)")

            # [2] 파일 주입 프로세스
            if uploaded_files:
                with st.sidebar.spinner("📦 선택하신 파일을 저장소에 저장하는 중..."):
                    try:
                        # 1. 기존 폴더 안의 낡은 파일들 청소
                        for f in os.listdir(SAVE_DIR):
                            file_path = os.path.join(SAVE_DIR, f)
                            if os.path.isfile(file_path):
                                os.remove(file_path)
                        
                        # 2. 새로운 파일들 안전하게 저장
                        for file_obj in uploaded_files:
                            with open(os.path.join(SAVE_DIR, file_obj.name), "wb") as f:
                                f.write(file_obj.getbuffer())
                        
                        # 3. 핵심 치트키: 업로더 위젯 비우기 및 리런
                        del st.session_state["demo_file_uploader"]
                        st.cache_data.clear()
                        st.toast("📂 데이터가 정상 주입되었습니다.")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"💥 파일 저장 중 에러 발생: {e}")

# [4] 메인 화면

if 'loaded_data' not in st.session_state:
    with st.spinner("데이터를 로드하는 중..."):
        # data/model 경로에서 파일 로드
        base_path = SAVE_DIR
        try:
            st.session_state['loaded_data'] = {
                'df_issue': pd.read_parquet(os.path.join(base_path, 'df_issue.parquet')),
                'df_pr': pd.read_parquet(os.path.join(base_path, 'df_pr.parquet')),
                'df_fork': pd.read_parquet(os.path.join(base_path, 'df_fork.parquet')),
                'issue_labels': pd.read_json(os.path.join(base_path, 'issue_labels.json'), typ='series'),
                'pr_labels': pd.read_json(os.path.join(base_path, 'pr_labels.json'), typ='series'),
                'df_issue_comment': pd.read_parquet(os.path.join(base_path, 'df_issue_comment.parquet')),
                'df_issues': pd.read_parquet(os.path.join(base_path, 'df_issues.parquet')),
                'df_pr_comment': pd.read_parquet(os.path.join(base_path, 'df_pr_comment.parquet')),
                'df_pr_review': pd.read_parquet(os.path.join(base_path, 'df_pr_review.parquet'))
            }
        except Exception as e:
            st.error(f"데이터 로드 실패: {e}")
            st.stop()

loaded_data = st.session_state['loaded_data']




if data is not None:
    df_issue, df_pr, df_fork, issue_labels, pr_labels, df_issue_comment, df_issues, df_pr_comment, df_pr_review = data
    st.set_page_config(layout="wide")
    st.title("🌌 오픈소스 영향력 스펙터클 매트릭스")
    st.write("K-Means로 분류된 **소통 테마(Issue/PR)**와 **정량적 인기(Star/Fork)**의 상관관계를 분석합니다.")



    # --- 3. 사용자 커스텀 가중치 (사이드바) ---
    st.sidebar.header("⚙️ 영향력 반응 커스텀")
    w_star = st.sidebar.slider("⭐ Star 가중치", 0.0, 10.0, 5.0)
    w_fork = st.sidebar.slider("🍴 Fork 가중치", 0.0, 10.0, 3.0)

    st.header("🎯 카테고리 조합별 저장소 분포 분석")
    st.write("분석하고 싶은 **이슈 테마**와 **PR 테마**를 선택하세요. 모든 저장소의 해당 테마 활동성을 계산합니다.")

    col_sel1, col_sel2 = st.columns(2)

    with col_sel1:
        # issue_labels의 value값들을 선택 리스트로 사용
        selected_issue_label = st.selectbox("🔍 분석할 Issue 테마", list(issue_labels.values()))
        # 선택된 라벨의 키(숫자)를 찾음
        sel_issue_idx = [k for k, v in issue_labels.items() if v == selected_issue_label][0]

    with col_sel2:
        selected_pr_label = st.selectbox("🔍 분석할 Pull Request 테마", list(pr_labels.values()))
        sel_pr_idx = [k for k, v in pr_labels.items() if v == selected_pr_label][0]

    # --- 2. 선택된 카테고리에 대한 저장소별 활동 점수 계산 ---
    # 각 저장소가 해당 클러스터(테마)에 속한 메시지를 몇 개나 가지고 있는지 카운트
    issue_activity = df_issue[df_issue['cluster'] == sel_issue_idx].groupby('repo_name').size().reset_index(name='issue_score')
    pr_activity = df_pr[df_pr['cluster'] == sel_pr_idx].groupby('repo_name').size().reset_index(name='pr_score')
    # --- 3. 데이터 통합 (전체 저장소 기준) ---

    # 1) 활동량 계산
    issue_activity = df_issue[df_issue['cluster'] == sel_issue_idx].groupby('repo_name').size().reset_index(name='issue_raw')
    pr_activity = df_pr[df_pr['cluster'] == sel_pr_idx].groupby('repo_name').size().reset_index(name='pr_raw')

    # 2) 저장소 영향력 데이터 (Fork 이벤트 데이터가 곧 활동량이므로, 여기서 집계)
    # 모든 저장소 목록을 확보하는 것이 중요합니다.
    repo_meta = df_fork.groupby('repo_name').size().reset_index(name='fork_count')
    # 만약 star_count 파일이 따로 없다면, fork_count를 기반으로 추정하거나 
    # 실제 데이터에 있는 star 컬럼을 사용해야 합니다.
    repo_meta['star_count'] = 100 # 추후 실제 컬럼으로 교체 필수

    # 3) 병합
    all_repos = pd.concat([df_issue['repo_name'], df_pr['repo_name'], repo_meta['repo_name']]).unique()
    dist_df = pd.DataFrame({'repo_name': all_repos})

    dist_df = dist_df.merge(issue_activity, on='repo_name', how='left').fillna(0)
    dist_df = dist_df.merge(pr_activity, on='repo_name', how='left').fillna(0)
    dist_df = dist_df.merge(repo_meta, on='repo_name', how='left').fillna(0)

    # 4) 가중치 계산 (로직 간소화)
    # 각 저장소의 기초 영향력 지수
    repo_weight = (dist_df['star_count'] * w_star) + (dist_df['fork_count'] * w_fork)

    # 가중치 적용된 활동 강도
    dist_df['issue_weighted'] = dist_df['issue_raw'] * repo_weight
    dist_df['pr_weighted'] = dist_df['pr_raw'] * repo_weight

    # 최종 지표 (Bubble 크기용)
    dist_df['Calculated_Influence'] = dist_df['issue_weighted'] + dist_df['pr_weighted']

    top_5_for_chart = dist_df.sort_values('Calculated_Influence', ascending=False).head(5)
    top_5_for_chart['rank'] = range(1, 6) # 순위 부여

    # 기본 그래프를 그립니다.
    fig_dist = px.scatter(
        dist_df[dist_df['Calculated_Influence'] > 0], # 유의미한 활동이 있는 저장소만
        x="issue_weighted",
        y="pr_weighted",
        size="Calculated_Influence",
        color="Calculated_Influence",
        hover_name="repo_name",
        labels={
            "issue_weighted": "가중치 적용 이슈 강도",
            "pr_weighted": "가중치 적용 PR 강도"
        },
        title=f"⭐ Star/🍴 Fork 영향력이 반영된 테마 분포",
        color_continuous_scale="Viridis",
        template="plotly_dark",
        # [특이하게 보여주기 1: 불투명도를 조절하여 다른 점들을 흐리게 만듭니다.]
        opacity=0.4 # 다른 점들은 흐리게
    )

    # [특이하게 보여주기 2: 상위 5개 저장소만 특별한 마커와 라벨로 추가합니다.]
    # Scatter trace를 하나 더 추가하는 방식입니다.
    fig_dist.add_trace(
        px.scatter(
            top_5_for_chart,
            x="issue_weighted",
            y="pr_weighted",
            size="Calculated_Influence",
            color="rank", # 순위별로 색상 지정
            color_continuous_scale="Reds", # 상위권은 빨간색 계열로 강조
            hover_name="repo_name",
            text="repo_name", # [핵심: 저장소 이름 라벨링]
            # [특이하게 보여주기 3: 마커 스타일 변경]
            # 마커 테두리를 진하게 하고 모양을 변경하여 강조
        ).update_traces(
            textposition="top center", # 라벨 위치 설정
            marker=dict(line=dict(width=2, color='white'), symbol='diamond') # 마커 모양 변경
        ).data[0]
    )
    # 시각적 가이드라인(평균선) 추가
    fig_dist.add_hline(
        y=dist_df['pr_weighted'].mean(), 
        line_dash="dot", 
        line_color="white", 
        annotation_text="PR 가중 활동 평균"
    )
    fig_dist.add_vline(
        x=dist_df['issue_weighted'].mean(), 
        line_dash="dot", 
        line_color="white", 
        annotation_text="Issue 가중 활동 평균"
    )

    fig_dist.update_layout(
        yaxis=dict(
            scaleanchor="x",
            scaleratio=1,  # 1:1 비율 (정사각형 유지)
        ),
        width=800,
        height=800,
    )


    st.plotly_chart(fig_dist, use_container_width=True)

    # --- 5. 분석 인사이트 ---
    # --- 5. 분석 인사이트 (수정) ---
    st.subheader("💡 데이터 분석 결과")

    # 가중치 계산이 완료된 dist_df에서 가장 영향력이 큰 저장소 찾기
    top_dist_repo = dist_df.sort_values('Calculated_Influence', ascending=False).iloc[0]

    st.write(f"""
    선택하신 **{selected_issue_label}**와 **{selected_pr_label}** 조합에서 가장 두드러지는 저장소는 **{top_dist_repo['repo_name']}**입니다. 
    이 저장소는 해당 이슈 영역에서 **{top_dist_repo['issue_raw']:.0f}회**, PR 영역에서 **{top_dist_repo['pr_raw']:.0f}회**의 활동을 기록하며 
    현재 설정된 가중치 기준으로 총 **{top_dist_repo['Calculated_Influence']:.2f}**의 영향력 지수를 확보했습니다.
    """)


    # --- 6. 상위 5개 저장소 상세 분석 ---
    st.subheader("🏆 상위 5개 저장소 성과 비교")

    # 영향력 기준 상위 5개 추출
    top_5_repos = dist_df.sort_values('Calculated_Influence', ascending=False).head(5)

    # 1) 표로 보기 좋게 출력
    st.table(top_5_repos[['repo_name', 'issue_raw', 'pr_raw', 'Calculated_Influence']])




    # --- 7. 저장소별 상세 이벤트 유형 분석 ---
    # --- 7. 저장소별 상세 이벤트 구성 분석 ---
    st.subheader("🔍 상위 5개 저장소 상세 이벤트 구성")
    # df_issue_comment, df_issues, df_pr_comment, df_pr_review
    # 1. 시각화 페이지에서 이벤트별로 다시 한번 확실하게 라벨링 (혹시 모를 누락 방지)
    df_issue_comment['event_type'] = 'IssueCommentEvent'
    df_issues['event_type'] = 'IssuesEvent'
    df_pr_comment['event_type'] = 'PullRequestReviewCommentEvent'
    df_pr_review['event_type'] = 'PullRequestReviewEvent'

    # 2. 이슈 통합 데이터와 PR 통합 데이터 생성
    df_issue_all = pd.concat([df_issue_comment, df_issues], ignore_index=True)
    df_pr_all = pd.concat([df_pr_comment, df_pr_review], ignore_index=True)

    # 3. 상위 5개 저장소 리스트 필터링
    top_5_names = top_5_repos['repo_name'].tolist()

    # 4. 상세 이벤트 구성 분석
    issue_detail = df_issue_all[df_issue_all['repo_name'].isin(top_5_names)].groupby(['repo_name', 'event_type']).size().unstack(fill_value=0)
    pr_detail = df_pr_all[df_pr_all['repo_name'].isin(top_5_names)].groupby(['repo_name', 'event_type']).size().unstack(fill_value=0)


    # 가중치 계산을 위한 계수
    weight_multiplier = (w_star * 10) + (w_fork * 10)

    # 1) 이벤트별 횟수(Count)와 가중치 점수(Score) 계산 
    # applymap 대신 map 사용!
    issue_score_df = issue_detail.map(lambda x: x * weight_multiplier)
    pr_score_df = pr_detail.map(lambda x: x * weight_multiplier)

    # 2) 횟수와 점수를 보기 좋게 표로 합치기
    # 나머지 로직은 그대로 유지하셔도 됩니다.
    issue_combined = pd.concat([issue_detail.add_suffix('_count'), issue_score_df.add_suffix('_score')], axis=1)
    pr_combined = pd.concat([pr_detail.add_suffix('_count'), pr_score_df.add_suffix('_score')], axis=1)

    # 컬럼 순서 정렬
    issue_combined = issue_combined.reindex(sorted(issue_combined.columns), axis=1)
    pr_combined = pr_combined.reindex(sorted(pr_combined.columns), axis=1)

    col1, col2 = st.columns(2)

    with col1:
        st.write("📊 이슈 이벤트 (횟수 vs 가중치 점수)")
        st.dataframe(issue_combined, use_container_width=True)

    with col2:
        st.write("📊 PR 이벤트 (횟수 vs 가중치 점수)")
        st.dataframe(pr_combined, use_container_width=True)

    # 2) 상세 비교 차트 (가로 막대 그래프)
    st.subheader("각 저장소의 '이슈 vs PR' 활동 비중 비교")
    fig_bar = px.bar(
        top_5_repos.melt(id_vars='repo_name', value_vars=['issue_raw', 'pr_raw']),
        x='value',
        y='repo_name',
        color='variable',
        orientation='h',
        barmode='group',
        labels={'value': '활동 횟수', 'repo_name': '저장소명', 'variable': '활동 유형'},
        template="plotly_dark"
    )
    st.plotly_chart(fig_bar, use_container_width=True)



elif loaded_data is not None:
    df_issue, df_pr, df_fork, issue_labels, pr_labels = [loaded_data[k] for k in ['df_issue', 'df_pr', 'df_fork', 'issue_labels', 'pr_labels']]
    df_issue_comment, df_issues, df_pr_comment, df_pr_review = [loaded_data[k] for k in ['df_issue_comment', 'df_issues', 'df_pr_comment', 'df_pr_review']]

    st.set_page_config(layout="wide")
    st.title("🌌 오픈소스 영향력 스펙터클 매트릭스")

    # 사이드바 및 선택 로직
    st.sidebar.header("⚙️ 영향력 반응 커스텀")
    w_star = st.sidebar.slider("⭐ Star 가중치", 0.0, 10.0, 5.0)
    w_fork = st.sidebar.slider("🍴 Fork 가중치", 0.0, 10.0, 3.0)

    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        selected_issue_label = st.selectbox("🔍 분석할 Issue 테마", list(issue_labels.values()))
        sel_issue_idx = [k for k, v in issue_labels.items() if v == selected_issue_label][0]
    with col_sel2:
        selected_pr_label = st.selectbox("🔍 분석할 Pull Request 테마", list(pr_labels.values()))
        sel_pr_idx = [k for k, v in pr_labels.items() if v == selected_pr_label][0]

    # --- 2. 데이터 통합 (표준화된 컬럼 사용) ---
    issue_act = df_issue[df_issue['cluster'] == int(sel_issue_idx)].groupby('repo_name').size().reset_index(name='issue_raw')
    pr_act = df_pr[df_pr['cluster'] == int(sel_pr_idx)].groupby('repo_name').size().reset_index(name='pr_raw')
    repo_meta = df_fork.groupby('repo_name').size().reset_index(name='fork_count')
    repo_meta['star_count'] = 100 

    all_repos = pd.concat([df_issue['repo_name'], df_pr['repo_name'], repo_meta['repo_name']]).unique()
    dist_df = pd.DataFrame({'repo_name': all_repos})

    dist_df = dist_df.merge(issue_act, on='repo_name', how='left').merge(pr_act, on='repo_name', how='left').merge(repo_meta, on='repo_name', how='left').fillna(0)

    # 가중치 적용
    repo_weight = (dist_df['star_count'] * w_star) + (dist_df['fork_count'] * w_fork)
    dist_df['issue_weighted'] = dist_df['issue_raw'] * repo_weight
    dist_df['pr_weighted'] = dist_df['pr_raw'] * repo_weight
    dist_df['Calculated_Influence'] = dist_df['issue_weighted'] + dist_df['pr_weighted']


    top_5_for_chart = dist_df.sort_values('Calculated_Influence', ascending=False).head(5)
    top_5_for_chart['rank'] = range(1, 6) # 순위 부여

    # 기본 그래프를 그립니다.
    fig_dist = px.scatter(
        dist_df[dist_df['Calculated_Influence'] > 0], # 유의미한 활동이 있는 저장소만
        x="issue_weighted",
        y="pr_weighted",
        size="Calculated_Influence",
        color="Calculated_Influence",
        hover_name="repo_name",
        labels={
            "issue_weighted": "가중치 적용 이슈 강도",
            "pr_weighted": "가중치 적용 PR 강도"
        },
        title=f"⭐ Star/🍴 Fork 영향력이 반영된 테마 분포",
        color_continuous_scale="Viridis",
        template="plotly_dark",
        # [특이하게 보여주기 1: 불투명도를 조절하여 다른 점들을 흐리게 만듭니다.]
        opacity=0.4 # 다른 점들은 흐리게
    )

    # [특이하게 보여주기 2: 상위 5개 저장소만 특별한 마커와 라벨로 추가합니다.]
    # Scatter trace를 하나 더 추가하는 방식입니다.
    fig_dist.add_trace(
        px.scatter(
            top_5_for_chart,
            x="issue_weighted",
            y="pr_weighted",
            size="Calculated_Influence",
            color="rank", # 순위별로 색상 지정
            color_continuous_scale="Reds", # 상위권은 빨간색 계열로 강조
            hover_name="repo_name",
            text="repo_name", # [핵심: 저장소 이름 라벨링]
            # [특이하게 보여주기 3: 마커 스타일 변경]
            # 마커 테두리를 진하게 하고 모양을 변경하여 강조
        ).update_traces(
            textposition="top center", # 라벨 위치 설정
            marker=dict(line=dict(width=2, color='white'), symbol='diamond') # 마커 모양 변경
        ).data[0]
    )

    # 시각적 가이드라인(평균선) 추가
    fig_dist.add_hline(
        y=dist_df['pr_weighted'].mean(), 
        line_dash="dot", 
        line_color="white", 
        annotation_text="PR 가중 활동 평균"
    )
    fig_dist.add_vline(
        x=dist_df['issue_weighted'].mean(), 
        line_dash="dot", 
        line_color="white", 
        annotation_text="Issue 가중 활동 평균"
    )

    fig_dist.update_layout(
        yaxis=dict(
            scaleanchor="x",
            scaleratio=1,  # 1:1 비율 (정사각형 유지)
        ),
        width=800,
        height=800,
    )


    st.plotly_chart(fig_dist, use_container_width=True)

    # --- 5. 분석 인사이트 ---
    # --- 5. 분석 인사이트 (수정) ---
    st.subheader("💡 데이터 분석 결과")

    # 가중치 계산이 완료된 dist_df에서 가장 영향력이 큰 저장소 찾기
    top_dist_repo = dist_df.sort_values('Calculated_Influence', ascending=False).iloc[0]

    st.write(f"""
    선택하신 **{selected_issue_label}**와 **{selected_pr_label}** 조합에서 가장 두드러지는 저장소는 **{top_dist_repo['repo_name']}**입니다. 
    이 저장소는 해당 이슈 영역에서 **{top_dist_repo['issue_raw']:.0f}회**, PR 영역에서 **{top_dist_repo['pr_raw']:.0f}회**의 활동을 기록하며 
    현재 설정된 가중치 기준으로 총 **{top_dist_repo['Calculated_Influence']:.2f}**의 영향력 지수를 확보했습니다.
    """)


    # --- 6. 상위 5개 저장소 상세 분석 ---
    st.subheader("🏆 상위 5개 저장소 성과 비교")

    # 영향력 기준 상위 5개 추출
    top_5_repos = dist_df.sort_values('Calculated_Influence', ascending=False).head(5)

    # 1) 표로 보기 좋게 출력
    st.table(top_5_repos[['repo_name', 'issue_raw', 'pr_raw', 'Calculated_Influence']])




    # --- 7. 저장소별 상세 이벤트 유형 분석 ---
    # --- 7. 저장소별 상세 이벤트 구성 분석 ---
    st.subheader("🔍 상위 5개 저장소 상세 이벤트 구성")
    # df_issue_comment, df_issues, df_pr_comment, df_pr_review
    # 1. 시각화 페이지에서 이벤트별로 다시 한번 확실하게 라벨링 (혹시 모를 누락 방지)
    df_issue_comment['event_type'] = 'IssueCommentEvent'
    df_issues['event_type'] = 'IssuesEvent'
    df_pr_comment['event_type'] = 'PullRequestReviewCommentEvent'
    df_pr_review['event_type'] = 'PullRequestReviewEvent'

    # 2. 이슈 통합 데이터와 PR 통합 데이터 생성
    df_issue_all = pd.concat([df_issue_comment, df_issues], ignore_index=True)
    df_pr_all = pd.concat([df_pr_comment, df_pr_review], ignore_index=True)

    # 3. 상위 5개 저장소 리스트 필터링
    top_5_names = top_5_repos['repo_name'].tolist()

    # 4. 상세 이벤트 구성 분석
    issue_detail = df_issue_all[df_issue_all['repo_name'].isin(top_5_names)].groupby(['repo_name', 'event_type']).size().unstack(fill_value=0)
    pr_detail = df_pr_all[df_pr_all['repo_name'].isin(top_5_names)].groupby(['repo_name', 'event_type']).size().unstack(fill_value=0)


    # 가중치 계산을 위한 계수
    weight_multiplier = (w_star * 10) + (w_fork * 10)

    # 1) 이벤트별 횟수(Count)와 가중치 점수(Score) 계산 
    # applymap 대신 map 사용!
    issue_score_df = issue_detail.map(lambda x: x * weight_multiplier)
    pr_score_df = pr_detail.map(lambda x: x * weight_multiplier)

    # 2) 횟수와 점수를 보기 좋게 표로 합치기
    # 나머지 로직은 그대로 유지하셔도 됩니다.
    issue_combined = pd.concat([issue_detail.add_suffix('_count'), issue_score_df.add_suffix('_score')], axis=1)
    pr_combined = pd.concat([pr_detail.add_suffix('_count'), pr_score_df.add_suffix('_score')], axis=1)

    # 컬럼 순서 정렬
    issue_combined = issue_combined.reindex(sorted(issue_combined.columns), axis=1)
    pr_combined = pr_combined.reindex(sorted(pr_combined.columns), axis=1)

    col1, col2 = st.columns(2)

    with col1:
        st.write("📊 이슈 이벤트 (횟수 vs 가중치 점수)")
        st.dataframe(issue_combined, use_container_width=True)

    with col2:
        st.write("📊 PR 이벤트 (횟수 vs 가중치 점수)")
        st.dataframe(pr_combined, use_container_width=True)

    # 2) 상세 비교 차트 (가로 막대 그래프)
    st.subheader("각 저장소의 '이슈 vs PR' 활동 비중 비교")
    fig_bar = px.bar(
        top_5_repos.melt(id_vars='repo_name', value_vars=['issue_raw', 'pr_raw']),
        x='value',
        y='repo_name',
        color='variable',
        orientation='h',
        barmode='group',
        labels={'value': '활동 횟수', 'repo_name': '저장소명', 'variable': '활동 유형'},
        template="plotly_dark"
    )
    st.plotly_chart(fig_bar, use_container_width=True)
else:
    st.warning("데이터가 로드되지 않았습니다. 잠시 후 다시 시도해주세요.")