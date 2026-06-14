import json
import pandas as pd
import os
import streamlit as st
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "use")

@st.cache_data
def load_event_data(event_type: str) -> pd.DataFrame:
    file_path = os.path.join(DATA_DIR, f"sampled_{event_type}.csv")
    
    # [디버깅 추가]
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        print(f"DEBUG: {event_type} 파일 로드 완료, 행 개수: {len(df)}")
        return df
    else:
        print(f"DEBUG: {event_type} 파일을 찾을 수 없음: {file_path}")
        return pd.DataFrame()

@st.cache_data
def get_available_events():
    """data/use 폴더 안의 CSV 파일들을 탐색하여 분석 가능한 이벤트 목록을 반환합니다."""
    if not os.path.exists(DATA_DIR):
        return []
    
    files = os.listdir(DATA_DIR)
    # .csv 파일만 추려서 파일명만 추출
    events = [f.replace('sampled_', '').replace('.csv', '') for f in files if f.startswith('sampled_')]
    return sorted(events)


@st.cache_data
def load_processed_data():
    # 1. 실제 폴더 안의 파일 목록 확인
    files_in_dir = os.listdir(DATA_DIR)
    
    def find_file(keyword):
        for f in files_in_dir:
            if keyword in f:
                return os.path.join(DATA_DIR, f)
        return None

    # 2. 키워드로 파일 경로 자동 매핑
    paths = {
        "IssueComment": find_file("IssueCommentEvent"),
        "Issues": find_file("IssuesEvent"),
        "PRReviewComment": find_file("PullRequestReviewCommentEvent"),
        "PRReview": find_file("PullRequestReviewEvent"),
        "Fork": find_file("ForkEvent")
    }

    # 파일이 하나라도 없으면 에러 메시지 출력
    for key, path in paths.items():
        if not path:
            st.error(f"'{key}' 관련 파일을 찾을 수 없습니다. 현재 폴더 파일 목록: {files_in_dir}")
            raise FileNotFoundError(f"'{key}' 키워드를 포함하는 파일을 폴더에서 찾지 못했습니다.")

    # 3. 데이터 로드 (이제 정확한 파일 경로를 사용)
    df_ic = pd.read_csv(paths["IssueComment"])
    df_i = pd.read_csv(paths["Issues"])
    df_prc = pd.read_csv(paths["PRReviewComment"])
    df_pr = pd.read_csv(paths["PRReview"])
    df_ic['event_type'] = 'IssueCommentEvent'
    df_i['event_type'] = 'IssuesEvent'
    df_prc['event_type'] = 'PullRequestReviewCommentEvent'
    df_pr['event_type'] = 'PullRequestReviewEvent'

    # 전처리 및 결합
    df_ic['combined_text'] = df_ic['issue_title'].fillna('') + " " + df_ic['comment_body'].fillna('')
    df_i['combined_text'] = df_i['issue_title'].fillna('')
    df_issue = pd.concat([df_ic[['repo_name', 'combined_text']], df_i[['repo_name', 'combined_text']]])
    
    df_prc['combined_text'] = df_prc['body'].fillna('')
    df_pr['combined_text'] = df_pr['body'].fillna('')
    df_pr_final = pd.concat([df_prc[['repo_name', 'combined_text']], df_pr[['repo_name', 'combined_text']]])
    path_fork = os.path.join(DATA_DIR, "sampled_ForkEvent.csv") # 정확한 파일명 확인 필요
    df_fork = pd.read_csv(path_fork)
    return df_issue, df_pr_final , df_fork , df_ic , df_i , df_prc , df_pr

import os
import pickle

# 임베딩 데이터를 저장할 경로
EMBEDDING_FILE = "embeddings_cache.pkl"
def save_all_results(data , SAVE_DIR):
    """
    get_clustered_data()에서 반환된 9개의 변수를 받아 
    각각 개별 parquet 파일로 저장합니다.
    """
    (df_issue, df_pr, df_fork, issue_labels, pr_labels, 
     df_issue_comment, df_issues, df_pr_comment, df_pr_review) = data
    
    # 각 데이터를 지정된 폴더에 개별 저장
    df_issue.to_parquet(os.path.join(SAVE_DIR, "df_issue.parquet"))
    df_pr.to_parquet(os.path.join(SAVE_DIR, "df_pr.parquet"))
    df_fork.to_parquet(os.path.join(SAVE_DIR, "df_fork.parquet"))
    df_issue_comment.to_parquet(os.path.join(SAVE_DIR, "df_issue_comment.parquet"))
    df_issues.to_parquet(os.path.join(SAVE_DIR, "df_issues.parquet"))
    df_pr_comment.to_parquet(os.path.join(SAVE_DIR, "df_pr_comment.parquet"))
    df_pr_review.to_parquet(os.path.join(SAVE_DIR, "df_pr_review.parquet"))
    
    # 라벨은 JSON으로 저장
    with open(os.path.join(SAVE_DIR, "issue_labels.json"), 'w', encoding='utf-8') as f:
        json.dump(issue_labels, f)
    with open(os.path.join(SAVE_DIR, "pr_labels.json"), 'w', encoding='utf-8') as f:
        json.dump(pr_labels, f)
        
    st.sidebar.success("✅ 모든 데이터 저장 완료!")
