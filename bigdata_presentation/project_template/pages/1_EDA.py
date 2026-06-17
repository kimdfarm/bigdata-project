# pages/1_📊_EDA.py
import streamlit as st
import pandas as pd
import plotly.express as px

# 🚀 정의해 둔 백엔드 모듈 임포트
from src.data_loader import load_event_data, get_available_events
from src.features import clean ,get_processed_df

st.set_page_config(page_title="GitHub Archive EDA", page_icon="📊", layout="wide")

st.title("📊 GitHub Archive 탐색적 데이터 분석 (EDA)")
st.markdown("---")

# 1. 현재 수집되어 사용 가능한 실제 이벤트 목록 확인
available_events = get_available_events()

if not available_events:
    st.warning("⚠️ 현재 저장소에 수집된 실제 데이터가 없습니다. 홈 화면(app.py)에서 실시간 수집을 진행하거나 데모 데이터를 먼저 주입해 주세요!")
else:
    st.sidebar.success("🟢 실제 데이터 연동 완료")
    
    # 💡 분석 옵션에 'Total(전체 이벤트 통합 분석)'을 가장 위에 추가합니다.
    search_options = ["Total (전체 이벤트 통합 분석)"] + available_events
    
    selected_option = st.sidebar.selectbox(
        "🔎 분석할 GitHub 이벤트 선택", 
        search_options,
        help="Total을 누르면 모든 이벤트의 트렌드를 한 번에 비교할 수 있습니다."
    )
    
    # ==============================================================================
    # 🏎️ 데이터 파이프라인 가동 및 데이터 취합 구역
    # ==============================================================================
    final_dfs = {}  # 선택된 모든 이벤트들의 데이터프레임을 저장할 주머니
    
    with st.spinner("📦 저장소에서 실제 데이터를 로드하여 정제하는 중..."):
        # 상황 1: 'Total'을 선택했을 때 -> 사용 가능한 모든 이벤트를 루프 돌며 취합
        if selected_option == "Total (전체 이벤트 통합 분석)":
            st.success("📂 **모든 수집 이벤트**의 실제 데이터를 통합 분석 중입니다.")
            for ev in available_events:
                raw_df = load_event_data(ev)
                cleaned_df = clean(raw_df)
                ready_df = get_processed_df(cleaned_df, ev)
                if not ready_df.empty:
                    ready_df['Event_Type'] = ev  # 구분을 위한 컬럼 추가
                    final_dfs[ev] = ready_df
        
        # 상황 2: 개별 이벤트를 선택했을 때
        else:
            st.success(f"📂 현재 **{selected_option}**의 실제 수집 데이터를 기반으로 데이터 가치를 탐색 중입니다.")
            raw_df = load_event_data(selected_option)
            cleaned_df = clean(raw_df)
            ready_df = get_processed_df(cleaned_df, selected_option)
            if not ready_df.empty:
                ready_df['Event_Type'] = selected_option
                final_dfs[selected_option] = ready_df

    # 분석할 데이터가 유효한지 최종 검증
    if not final_dfs:
        st.error("❌ 분석 대상 데이터 파일이 비어있거나 읽어올 수 없습니다.")
    else:
        # 화면 시각화를 위해 데이터프레임을 합침
        combined_df = pd.concat(final_dfs.values(), ignore_index=True)
        
        # ==============================================================================
        # 📊 요약 메트릭
        # ==============================================================================
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("총 분석 행(Row) 수", f"{len(combined_df):,} 개")
        with col2:
            st.metric("연동된 이벤트 종류", f"{combined_df['Event_Type'].nunique()} 개")
        with col3:
            if 'repo_name' in combined_df.columns:
                st.metric("고유 레포지토리 수", f"{combined_df['repo_name'].nunique():,} 개")
            else:
                st.metric("고유 레포지토리 수", "데이터 내 컬럼 없음")

        # ==============================================================================
        # 📋 [🔥 핵심 튜닝] 데이터 샘플 미리보기 (이벤트별 가치 컬럼 분리 독립 매핑)
        # ==============================================================================
        # ==============================================================================
        # 📋 [수정됨] 선택한 이벤트의 데이터를 독립적으로 로드하여 payload 샘플링
        # ==============================================================================
        st.markdown("### 📋 데이터 샘플 미리보기 (선택된 이벤트 오리지널 데이터)")
        
        if selected_option == "Total (전체 이벤트 통합 분석)":
            st.info("ℹ️ Total 모드에서는 여러 이벤트가 혼합되어 있어, 개별 데이터의 상세 payload를 보여드리기 어렵습니다. 상세 확인을 원하시면 사이드바에서 특정 이벤트를 선택해 주세요.")
        else:
            # 통합된 combined_df가 아니라, 선택한 이벤트를 다시 독립 로드하여 payload를 풂
            raw_preview_df = load_event_data(selected_option)
            preview_df = get_processed_df(raw_preview_df, selected_option)
            
            # 각 이벤트별 가치 있는 컬럼만 쏙 골라 출력
            st.dataframe(preview_df.head(5), use_container_width=True)
        
        # [데이터 샘플 미리보기 코드 뒤에 붙이세요]

        if selected_option == "ForkEvent":
            st.markdown("---")
            st.markdown("### 🏆 가장 많이 포크된 저장소 Top 10")
            
            # 1. 컬럼명이 'forkee_full_name'으로 확인됨
            target_col = 'forkee_full_name' 
            
            if target_col in raw_df.columns:
                # 2. 빈도수 집계
                top_forked = raw_df[target_col].value_counts().reset_index()
                top_forked.columns = ['저장소 이름', '포크 횟수']
                top_10 = top_forked.head(10)
                
                # 3. 가로 막대 그래프 그리기
                fig = px.bar(
                    top_10, 
                    x='포크 횟수', 
                    y='저장소 이름', 
                    orientation='h',
                    title="가장 인기 있는 포크 대상 저장소 Top 10",
                    text_auto=True,
                    color='포크 횟수',
                    color_continuous_scale='Blues'
                )
                # 상위 순위가 위로 오게 정렬
                fig.update_layout(yaxis=dict(autorange="reversed")) 
                st.plotly_chart(fig, use_container_width=True)
                
                st.write("상세 순위 데이터:")
                st.dataframe(top_10, use_container_width=True)
            else:
                st.error(f"데이터에 '{target_col}' 컬럼을 찾을 수 없습니다. 현재 컬럼: {raw_df.columns.tolist()}")

        elif selected_option == "IssuesEvent":
# 1. 텍스트 길이 사전 계산
            raw_df['title_length'] = raw_df['issue_title'].fillna("").str.len()
            
            st.markdown("### 📊 레포지토리별 이슈 통계")
            
            # 1. 모든 레포지토리 리스트 확보
            # 1. 레포지토리별 이슈 개수 계산
            repo_counts = raw_df['repo_name'].value_counts() # 내림차순 자동 정렬됨

            # 2. 셀렉트박스에 표시할 이름 생성 (이름 + 개수)
            # 예: "LGU-SE-Internal/opentelemetry-demo (149개)"
            repo_options = [f"{repo} ({count}개)" for repo, count in repo_counts.items()]

            # 3. 멀티셀렉트 생성
            selected_options = st.multiselect(
                "분석할 저장소를 선택하세요 (이슈 개수 순 정렬):", 
                repo_options, 
                default=repo_options[:10] # 상위 10개 자동 선택
            )

            # 4. 선택된 옵션에서 저장소 이름만 추출 (괄호 부분 제거)
            selected_repos = [opt.split(" (")[0] for opt in selected_options]
            # 3. 선택된 저장소만 필터링
            if selected_repos:
                subset_df = raw_df[raw_df['repo_name'].isin(selected_repos)]
                
                # 4. Boxplot 시각화
                st.markdown(f"### 📦 선택된 저장소의 이슈 제목 길이 분포")
                
                plot_df = subset_df.copy()

                # 2. repo_counts에서 각 저장소별 개수를 가져와 매핑
                # repo_counts는 이미 series 형태이므로 바로 index로 접근 가능합니다.
                plot_df['repo_display'] = plot_df['repo_name'].apply(
                    lambda x: f"{x} ({repo_counts[x]}개)"
                )

                # 3. Boxplot 시각화 (범례까지 함께 적용)
                fig = px.box(
                    plot_df, 
                    x='repo_display', 
                    y='title_length', 
                    color='repo_display', 
                    title="선택한 저장소별 이슈 제목 길이 분포 (이슈 개수 포함)",
                    labels={'repo_display': '저장소 (이슈 개수)', 'title_length': '글자 수'}
                )

                # [선택 사항] 그래프 정렬: 개수가 많은 순서대로 x축을 정렬하고 싶다면
                fig.update_layout(xaxis={'categoryorder':'total descending'})

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("비교할 저장소를 하나 이상 선택해 주세요.")
        
        elif selected_option == "IssueCommentEvent":
            # 1. 댓글의 글자 수 계산
            raw_df['comment_length'] = raw_df['comment_body'].fillna("").str.len()
            
            st.markdown("### 🗣️ 저장소별 댓글 상세도 분석")
            
            # 2. 레포지토리별 댓글 개수 산출 (내림차순)
            repo_counts = raw_df['repo_name'].value_counts()
            repo_options = [f"{repo} ({count}개)" for repo, count in repo_counts.items()]
            
            # 3. 저장소 선택 UI
            selected_options = st.multiselect(
                "분석할 저장소를 선택하세요 (댓글 개수 순 정렬):", 
                repo_options, 
                default=repo_options[:5]
            )
            
            selected_repos = [opt.split(" (")[0] for opt in selected_options]
            
            # 4. 선택된 데이터만 필터링 및 시각화
            if selected_repos:
                subset_df = raw_df[raw_df['repo_name'].isin(selected_repos)].copy()
                
                # 범례에 개수 표시를 위한 컬럼 생성
                subset_df['repo_display'] = subset_df['repo_name'].apply(
                    lambda x: f"{x} ({repo_counts[x]}개)"
                )
                
                st.markdown(f"### 📦 선택된 {len(selected_repos)}개 저장소의 댓글 길이 분포")
                
                fig = px.box(
                    subset_df, 
                    x='repo_display', 
                    y='comment_length', 
                    color='repo_display',
                    title="저장소별 댓글 길이 분포",
                    labels={'repo_display': '저장소 (댓글 개수)', 'comment_length': '댓글 글자 수'}
                )
                fig.update_layout(xaxis={'categoryorder':'total descending'})
                st.plotly_chart(fig, use_container_width=True)
                
                st.write("Boxplot의 박스 길이가 길거나 상단에 점이 많을수록, 단순한 반응을 넘어선 상세한 기술 토론이 활발한 곳입니다.")
                
            else:
                st.info("분석할 저장소를 위에서 선택해 주세요.")
                    
        elif selected_option == "PullRequestEvent":
            import plotly.express as px
            def plot_rank_based_repo_analysis(df):
                st.markdown("### ⚙️ 저장소 순위 분석 설정")
                df['Status'] = df['merged'].apply(lambda x: 'Merged' if x else 'Not Merged')
                
                # 1. 저장소별 활동량 순위 계산
                repo_activity = df.groupby('base_repo').size().reset_index(name='Total_Count')
                repo_activity = repo_activity.sort_values('Total_Count', ascending=False).reset_index(drop=True)
                repo_activity['Rank'] = repo_activity.index + 1
                
                total_repos = len(repo_activity)
                st.write(f"현재 분석 가능한 총 저장소 개수: **{total_repos}개**")
                
                # 2. 순위 입력 구간 (왼쪽 N, 오른쪽 M 대신 시작순위, 끝순위)
                col1, col2 = st.columns(2)
                with col1:
                    # min_value/max_value를 입력받을 때 적용하지 않습니다.
                    start_rank = st.number_input("시작 순위 (N)", value=1, step=1)
                with col2:
                    end_rank = st.number_input("종료 순위 (M)", value=10, step=1)
                                
                if start_rank > end_rank:
                    st.warning("⚠️ 시작 순위가 종료 순위보다 클 수 없습니다. 조정해주세요!")
                    # 자동으로 조정되길 원하시면 아래처럼 하셔도 됩니다.
                    # end_rank = start_rank 
                elif end_rank > total_repos:
                    st.warning(f"⚠️ 총 {total_repos}개 저장소를 초과할 수 없습니다.")               
                else:
                    # 3. 데이터 필터링
                    selected_repos = repo_activity[(repo_activity['Rank'] >= start_rank) & (repo_activity['Rank'] <= end_rank)]['base_repo']
                    df_filtered = df[df['base_repo'].isin(selected_repos)]
                    
                    st.write(f"분석 중: **{start_rank}위 ~ {end_rank}위** (총 {len(selected_repos)}개 저장소)")

                    # 4. 분석 결과 그래프
                    # 명확하게 비교하고 결측치까지 처리
                    df['Status'] = df['merged'].map({True: 'Merged', False: 'Not Merged'}).fillna('Not Merged')
                    repo_order = selected_repos.tolist()
                    # 그래프 시각화 로직
                    fig1 = px.bar(
                        df_filtered.groupby(['base_repo', 'Status']).size().reset_index(name='Count'), 
                        x='base_repo', y='Count', color='Status', barmode='group', 
                        title="저장소별 병합 상태",
                        category_orders={'base_repo': repo_order} # 추가
                    )

                    fig2 = px.bar(
                        df_filtered.groupby(['base_repo', 'action']).size().reset_index(name='Count'), 
                        x='base_repo', y='Count', color='action', barmode='group', 
                        title="저장소별 PR 액션",
                        category_orders={'base_repo': repo_order} # 추가
                    )
                    
                    st.plotly_chart(fig1, use_container_width=True)
                    st.plotly_chart(fig2, use_container_width=True)
            plot_rank_based_repo_analysis(combined_df)
            st.markdown("""
### Action 값,역할 (무엇을 의미하는가?)
* **opened**: 개발자가 처음으로 PR을 생성했을 때 발생합니다. 분석의 시작점입니다.
* **closed**: PR이 닫혔음을 의미합니다. 주의: 이것이 꼭 병합된 것은 아닙니다. 그냥 거절되었거나, 사용자가 수동으로 닫았을 수도 있습니다.
* **labeled**: PR에 태그(레이블)가 붙었을 때 발생합니다. (예: bug, enhancement)
* **unlabeled**: 붙어있던 레이블이 제거되었을 때 발생합니다.
* **assigned**: 누군가 이 PR의 리뷰어/담당자로 지정되었을 때 발생합니다.
* **reopened**: 닫혔던 PR을 다시 열었을 때 발생합니다.
""")

        elif selected_option == "PullRequestReviewCommentEvent":
            def plot_integrated_review_analysis(df):
            # 1. 공통 데이터 전처리 및 구간 설정
                repo_stats = df.groupby('repo_name').size().reset_index(name='total_reviews')
                repo_stats = repo_stats.sort_values('total_reviews', ascending=False).reset_index(drop=True)
                repo_stats['rank'] = repo_stats.index + 1
                
                st.markdown("### ⚙️ 분석 구간 설정 (전체 공통)")
                col1, col2 = st.columns(2)
                with col1: 
                    n = st.number_input("시작 순위 (N)", min_value=1, value=1, step=1, key="start_rank_all")
                with col2: 
                    # m의 시작값을 n과 10 중 큰 값으로 설정하여 에러 방지
                    m = st.number_input("종료 순위 (M)", min_value=n, value=max(10, n), step=1, key="end_rank_all")
                target_repos = repo_stats[(repo_stats['rank'] >= n) & (repo_stats['rank'] <= m)]['repo_name']
                df_filtered = df[df['repo_name'].isin(target_repos)].copy()
                
                # [새로운 로직] 경로 깊이 계산 및 속성 추출
                # 슬래시(/) 개수를 세어 깊이를 산출 (예: a/b/c.js -> 깊이 3)
                df_filtered['path_depth'] = df_filtered['path'].astype(str).apply(lambda x: x.count('/') + 1)
                df_filtered['file_ext'] = df_filtered['path'].astype(str).apply(lambda x: x.split('.')[-1] if '.' in x else 'unknown')
                df_filtered['is_bot'] = df_filtered['reviewer_type'].apply(lambda x: str(x).lower() == 'bot')
                
                # 2. [섹션 1] 리뷰어 유형 분석
                st.markdown("### 🤖 리뷰어 유형 분석")
                review_counts = df_filtered.groupby(['repo_name', 'is_bot']).size().reset_index(name='Review_Count')
                review_counts['Type'] = review_counts['is_bot'].map({True: 'Bot', False: 'Human'})
                repo_order = df_filtered['repo_name'].unique().tolist()
                fig1 = px.bar(review_counts, x='repo_name', y='Review_Count', color='Type', barmode='stack',category_orders={"repo_name": repo_order})
                
                
                st.plotly_chart(fig1, use_container_width=True)
                
                # 3. [섹션 2] 파일 경로 깊이 및 타입별 리뷰 분포
                st.markdown("### 📂 파일 경로 깊이 및 타입별 리뷰 분석")
                # Boxplot: 저장소별로 path_depth를 시각화하여 리뷰가 주로 어느 깊이(구조)에서 일어나는지 확인
                fig2 = px.box(
    df_filtered, x='repo_name', y='path_depth', color='file_ext',
    title="저장소별 파일 경로 깊이(Depth) 및 확장자 분포",
    points="all",
    category_orders={"repo_name": repo_order} # 동일한 순서로 고정
)
                fig2.update_layout(xaxis_tickangle=-45, yaxis_title="경로 깊이 (Depth)")
                st.plotly_chart(fig2, use_container_width=True)
            # 실행
            plot_integrated_review_analysis(combined_df)

        elif selected_option == "PullRequestReviewEvent":
            def plot_approval_scatter_analysis(df):
                # 1. 공통 전처리: 저장소별 리뷰 수 기준 순위 산정
                repo_stats = df.groupby('repo_name').size().reset_index(name='total_reviews')
                repo_stats = repo_stats.sort_values('total_reviews', ascending=False).reset_index(drop=True)
                repo_stats['rank'] = repo_stats.index + 1
                
                # 2. 구간 설정 (N위 ~ M위)
                st.markdown("### ⚙️ 분석 구간 설정")
                col1, col2 = st.columns(2)
                with col1: n = st.number_input("시작 순위 (N)", min_value=1, value=1, step=1, key="start_apr_rank")
                with col2: m = st.number_input("종료 순위 (M)", min_value=n, value=max(10, n), step=1, key="end_apr_rank")
                
                # 선택된 저장소 필터링
                target_repos = repo_stats[(repo_stats['rank'] >= n) & (repo_stats['rank'] <= m)]['repo_name']
                df_filtered = df[df['repo_name'].isin(target_repos)].copy()
                
                # 3. 승인율(Approved Rate) 계산
                df_filtered['is_approved'] = (df_filtered['review_state'] == 'approved').astype(int)
                approval_data = df_filtered.groupby('repo_name').agg(
                    total_reviews=('review_state', 'count'),
                    approval_rate=('is_approved', 'mean')
                ).reset_index()
                
                # 4. 시각화 (Scatter Plot)
                st.markdown(f"### 🎯 저장소별 승인율 분포 (상위 {n}~{m}위 저장소)")
                
                fig = px.scatter(
                    approval_data,
                    x='total_reviews',       # 활동량(리뷰 수)
                    y='approval_rate',       # 승인율
                    size='total_reviews',    # 버블 크기
                    color='repo_name',       # 저장소별 구분
                    hover_name='repo_name',
                    title="리뷰 활동량 대비 승인율 관계",
                    labels={'total_reviews': '총 리뷰 횟수', 'approval_rate': '승인율(0~1)'}
                )
                
                # 승인율 평균선 추가 (참고용)
                fig.add_hline(y=approval_data['approval_rate'].mean(), line_dash="dash", line_color="gray", annotation_text="전체 평균 승인율")
                
                st.plotly_chart(fig, use_container_width=True)

            plot_approval_scatter_analysis(combined_df)

        elif selected_option == "WatchEvent":
            def plot_watch_event_analysis(df):
            # 1. 저장소별 Star 개수 집계
                repo_stats = df.groupby('repo_name').size().reset_index(name='star_count')
                repo_stats = repo_stats.sort_values('star_count', ascending=False).reset_index(drop=True)
                repo_stats['rank'] = repo_stats.index + 1
                
                # 2. 상위 필터링 구간 설정
                st.markdown("### ⚙️ 분석 구간 설정 (상위 N~M위 저장소)")
                col1, col2 = st.columns(2)
                with col1: n = st.number_input("시작 순위 (N)", min_value=1, value=1, step=1, key="start_watch_rank")
                with col2: m = st.number_input("종료 순위 (M)", min_value=n, value=max(10, n), step=1, key="end_watch_rank")
                
                target_repos = repo_stats[(repo_stats['rank'] >= n) & (repo_stats['rank'] <= m)]
                
                # 3. [상단] 선택된 상위 저장소 막대 그래프
                st.markdown(f"### ⭐ 상위 {n}~{m}위 저장소 Star 개수")
                fig1 = px.bar(target_repos, x='repo_name', y='star_count', color='star_count', 
                            title=f"상위 {n}~{m}위 저장소 Star 개수 비교")
                st.plotly_chart(fig1, use_container_width=True)
                
                # 4. [하단] 전체 저장소 Star 개수 분포 (Boxplot)
                st.markdown("### 📦 전체 저장소 Star 분포 (전체 데이터 기반)")
                fig2 = px.box(
                    repo_stats, 
                    y='star_count', 
                    title="전체 저장소 Star 개수 통계적 분포",
                    points="outliers" # 이상치(매우 인기 있는 저장소)만 표시하여 가독성 확보
                )
                st.plotly_chart(fig2, use_container_width=True)
            plot_watch_event_analysis(combined_df)
 
        # ==============================================================================
        # 📈 시간대별 이벤트 발생 추이 (원본 유지)
        # ==============================================================================
        if 'created_at' in combined_df.columns and selected_option != "PullRequestEvent" :
            st.markdown("---")
            st.markdown("### 📈 시간대별 이벤트 발생 추이 (영국 표준시 UTC 기준)")
            
            # 1. 데이터를 합친 직후에 무조건 datetime으로 강제 변환
            combined_df['created_at'] = pd.to_datetime(combined_df['created_at'], errors='coerce')

            # 2. 혹시라도 변환이 안 된 데이터가 있다면(NaT), 전체 데이터에서 삭제하거나 0시로 채움
            combined_df = combined_df.dropna(subset=['created_at'])

            # 3. 이제 타입을 확인 (debug)
            st.write("변환 후 타입:", combined_df['created_at'].dtype) 

            # 4. 이제 .dt 접근자 사용
            combined_df['hour'] = combined_df['created_at'].dt.hour
            
            hourly_event_counts = combined_df.groupby(['Event_Type', 'hour']).size().reset_index(name='Event Count')
            hourly_event_counts = hourly_event_counts.sort_values(by='hour')
            
            # 시각화 (경고가 떴던 use_container_width 수정 적용)
            fig = px.line(hourly_event_counts, x='hour', y='Event Count', color='Event_Type', markers=True)
            st.plotly_chart(fig, use_container_width=True) # 여기는 width='stretch' 대신 기존 방식 유지해도 됩니다.
        elif selected_option == "PullRequestEvent":
            @st.cache_data
            def get_timeline_data(df, freq):
                df['created_at'] = pd.to_datetime(df['created_at'])
                return df.groupby([pd.Grouper(key='created_at', freq=freq), 'action']).size().reset_index(name='count')

            def plot_advanced_timeline(df):
                st.markdown("### 🕒 상세 시간 단위 타임라인 분석")
                
                col1, col2 = st.columns(2)
                with col1:
                    # H(시간) 옵션 추가
                    unit_type = st.selectbox("기준 단위 선택", ["H (시간)", "D (일)", "W (주)", "M (월)", "Y (년)"])
                with col2:
                    n = st.number_input("묶을 간격 (n)", min_value=1, value=1, step=1)
                    
                # 시간 단위 매핑 (H는 시간 단위)
                freq_map = {
                    "H (시간)": f"{n}h",    # 대문자 H -> 소문자 h
                    "D (일)": f"{n}D", 
                    "W (주)": f"{n}W", 
                    "M (월)": f"{n}MS",     # MS(Month Start)는 대문자 그대로 사용 가능
                    "Y (년)": f"{n}YS"      # YS(Year Start)도 대문자 그대로 사용 가능
                }
                # 캐시 함수 호출
                timeline_df = get_timeline_data(df, freq_map[unit_type])
                
                # 시각화
                fig = px.line(
                    timeline_df, 
                    x='created_at', 
                    y='count', 
                    color='action', 
                    markers=True,
                    title=f"시간 흐름에 따른 PR 액션 변화 (간격: {n}{unit_type.split(' ')[0]})"
                )
                
                fig.update_layout(xaxis_title="시간", yaxis_title="발생 횟수")
                st.plotly_chart(fig, use_container_width=True)

            # 호출
            if selected_option == "PullRequestEvent":
                plot_advanced_timeline(combined_df)            
        
        # ==============================================================================
        # 🌍 글로벌 개발자 활동 시간대(시차) 가이드 안내판 (원본 유지)
        # ==============================================================================
        st.markdown("---")
        st.markdown("### 🌍 글로벌 주요 국가별 시차 및 개발 피크 타임 가이드")
        st.info("💡 **수집 데이터는 영국 표준시(UTC) 기준**으로 기록됩니다. 위 차트의 피크 타임이 어느 나라인지 분석할 때 아래의 표준 근무 시간(09:00~18:00) 대조표를 참고해 보세요!")
        
        geo_col1, geo_col2 = st.columns(2)
        with geo_col1:
            st.markdown("""
            * **🇪🇺 유럽 / 영국 (UTC+0 ~ UTC+1)**
                * **현지 근무 시간:** 차트상의 **08:00 ~ 17:00** 부근
                * *특징:* 차트 중반부 이후 완만하게 상승하는 구간에 기여합니다.
            
            * **🇺🇸 미국 동부/서부 (UTC-5 ~ UTC-8)**
                * **현지 근무 시간:** 차트상의 **14:00 ~ 익일 02:00** 부근
                * *특징:* 국내 새벽 시간대에 발생하는 대규모 오픈소스 트래픽의 중심지입니다.
            """)
            
        with geo_col2:
            st.markdown("""
            * **🇰🇷 한국 / 🇯🇵 일본 (UTC+9)**
                * **현지 근무 시간:** 차트상의 **00:00(자정) ~ 09:00** 부근
                * *특징:* 차트의 초반부(0시~9시)에 발생하는 급증 구간은 주로 아시아권 개발자들의 주간 활동입니다.
                
            * **🇨🇳 중국 (UTC+8)**
                * **현지 근무 시간:** 차트상의 **01:00 ~ 10:00** 부근
                * *특징:* 아시아 대륙의 대규모 푸시 및 포크 트래픽의 상당수를 차지합니다.
            """)

        # ==============================================================================
        # 🔍 컬럼별 데이터 누락(Null) 분포 상태 (원본 유지)
        # ==============================================================================
        st.markdown("### 🔍 컬럼별 데이터 누락(Null) 분포 상태")
        null_counts = combined_df.isnull().sum().reset_index()
        null_counts.columns = ['컬럼명', '결측치 개수']
        fig_bar = px.bar(null_counts, x='컬럼명', y='결측치 개수', text_auto=True)
        st.plotly_chart(fig_bar, use_container_width=True)