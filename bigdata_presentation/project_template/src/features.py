# src/features.py


import streamlit as st  

import numpy as np
import pandas as pd
import json
from sentence_transformers import SentenceTransformer
from sklearn.mixture import GaussianMixture
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA


@st.cache_data
def clean(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    if "id" in df.columns:
        df = df.dropna(subset=["id"])
    df = df.drop_duplicates(subset=["id"])
    return df

# 🎯 통합 분기 함수 (여기에 모든 이벤트를 추가)
@st.cache_data
def get_processed_df(df: pd.DataFrame, event_type: str) -> pd.DataFrame:
    df = clean(df)            
    return df




def get_sbert_model():
    if 'sbert_model' not in st.session_state:
        # 1. 더 가볍고 빠른 MiniLM 모델 사용
        st.session_state['sbert_model'] = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    return st.session_state['sbert_model']

def get_top_keywords(df, n_clusters, top_n=3):
    """각 클러스터 내에서 TF-IDF가 높은 단어를 추출하여 라벨 생성"""
    labels = {}
    # 텍스트가 너무 짧거나 없으면 기본값 설정
    vectorizer = TfidfVectorizer(stop_words='english', max_features=500) 
    
    for i in range(n_clusters):
        cluster_df = df[df['cluster'] == i]
        if len(cluster_df) < 2: # 데이터가 너무 적으면
            labels[i] = f"Cluster {i} (기타)"
            continue
            
        texts = cluster_df['combined_text'].fillna("").tolist()
        tfidf_matrix = vectorizer.fit_transform(texts)
        
        # 단어별 점수 합계
        sums = tfidf_matrix.sum(axis=0)
        feature_names = vectorizer.get_feature_names_out()
        
        # 점수 높은 순으로 정렬
        ranking = sorted(zip(feature_names, sums.A1), key=lambda x: x[1], reverse=True)
        top_words = [word for word, score in ranking[:top_n]]
        
        # 키워드를 쉼표로 연결하여 라벨로 사용 (예: "bug, fix, error")
        labels[i] = ", ".join(top_words)
        
    return labels





def apply_use(df, n=10):
    model_sbert = get_sbert_model()
    texts = df['combined_text'].fillna("").astype(str).tolist()
    
    # 1. UI 요소 생성
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # 2. 직접 배치 처리 (tqdm 대신 streamlit progressbar 활용)
    batch_size = 64
    total_batches = (len(texts) + batch_size - 1) // batch_size
    embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        batch_embeddings = model_sbert.encode(batch, show_progress_bar=False)
        embeddings.append(batch_embeddings)
        
        # UI 업데이트
        if progress_bar and status_text:
            current_batch = (i // batch_size) + 1
            progress = current_batch / total_batches
            progress_bar.progress(progress)
            status_text.write(f"⚙️ 배치 처리 중: {current_batch} / {total_batches}")

    # 모든 배치 합치기
    embeddings = np.vstack(embeddings)
    
    status_text.success("임베딩 완료!")
    
    # 3. PCA로 차원 축소 (768 -> 50)
    # GMM은 고차원 벡터에서 계산량이 매우 많으므로, 차원을 줄이면 속도가 비약적으로 상승합니다.
    pca = PCA(n_components=50)
    reduced_embeddings = pca.fit_transform(embeddings)
    
    # 4. GMM 적용 (차원 축소된 데이터 사용)
    gmm = GaussianMixture(n_components=n, random_state=42, covariance_type='full')
    gmm.fit(reduced_embeddings)
    
    probs = gmm.predict_proba(reduced_embeddings)
    
    for i in range(n):
        df[f'Theme_{i}_weight'] = probs[:, i]
        
    df['cluster'] = np.argmax(probs, axis=1)
    labels = get_top_keywords(df, n)
    
    return df, labels
import os
def load_data_from_disk(SAVE_DIR):
    data_dict = {}
    
    # 1. Parquet 파일 로드 (데이터프레임들)
    parquet_files = ['df_issue', 'df_pr', 'df_fork', 'df_issue_comment', 'df_issues', 'df_pr_comment', 'df_pr_review']
    for name in parquet_files:
        path = os.path.join(SAVE_DIR, f"{name}.parquet")
        if os.path.exists(path):
            data_dict[name] = pd.read_parquet(path)
            
    # 2. JSON 파일 로드 (라벨 정보들) - 여기가 중요합니다!
    for key in ['issue_labels', 'pr_labels']:
            path = os.path.join(SAVE_DIR, f"{key}.json")
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    # 1. f.read()가 아니라 반드시 json.load(f)를 사용해야 합니다.
                    data_dict[key] = json.load(f) 
                    
                    # 2. 혹시나 하는 마음에 디버깅 출력 (콘솔 확인)
                    print(f"{key} 타입 확인: {type(data_dict[key])}")
    
    return data_dict
