# src/features.py
import joblib

import streamlit as st  

import numpy as np
import pandas as pd
import json
from sentence_transformers import SentenceTransformer
from sklearn.mixture import GaussianMixture
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

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





def apply_use(df, n=10 , type="issue"):
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
    
    # 3. PCA로 차원 축소 90%
    # GMM은 고차원 벡터에서 계산량이 매우 많으므로, 차원을 줄이면 속도가 비약적으로 상승합니다.
    pca = PCA(n_components=0.9)
    reduced_embeddings = pca.fit_transform(embeddings)
    scaler = StandardScaler()
    scaled_embeddings = scaler.fit_transform(reduced_embeddings)
    import joblib
    
    # 4. GMM 적용 (차원 축소된 데이터 사용)
    gmm = GaussianMixture(
    n_components=n, 
    random_state=42, 
    covariance_type='full', 
    reg_covar=1e-3  # 기본값은 1e-6인데, 1e-3 정도로 늘려보세요.
)
    gmm.fit(scaled_embeddings)
    # 2. 폴더가 없으면 하위 폴더까지 통째로 자동 생성하는 코드 추가
    os.makedirs(rf'bigdata_presentation\project_template\data\pred\{type}', exist_ok=True)
    # ================= [이 부분을 추가합니다] =================
    # 학습된 3개의 모델을 파일로 저장 (꺼내기)
    joblib.dump(pca, rf'bigdata_presentation\project_template\data\pred\{type}\trained_pca.pkl')
    joblib.dump(scaler, rf'bigdata_presentation\project_template\data\pred\{type}\trained_scaler.pkl')
    joblib.dump(gmm, rf'bigdata_presentation\project_template\data\pred\{type}\trained_gmm.pkl')
    # =========================================================
    probs = gmm.predict_proba(scaled_embeddings)
    
    for i in range(n):

        df[f'Theme_{i}_weight'] = probs[:, i]
        
    df['cluster'] = np.argmax(probs, axis=1)
    labels = get_top_keywords(df, n)
    
    return df, labels
import os

def load_data_from_disk(SAVE_DIR):
    data_dict = {}
    
    # 필수 파일 리스트 정의
    parquet_files = ['df_issue', 'df_pr', 'df_fork', 'df_issue_comment', 'df_issues', 'df_pr_comment', 'df_pr_review']
    json_files = ['issue_labels', 'pr_labels']
    
    # 1. Parquet 로드
    for name in parquet_files:
        path = os.path.join(SAVE_DIR, f"{name}.parquet")
        if os.path.exists(path):
            data_dict[name] = pd.read_parquet(path)
        else:
            # 파일이 없으면 빈 데이터프레임 할당 (에러 방지)
            data_dict[name] = pd.DataFrame() 
            
    # 2. JSON 로드
    for key in json_files:
        path = os.path.join(SAVE_DIR, f"{key}.json")
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data_dict[key] = json.load(f)
        else:
            # 파일이 없으면 빈 딕셔너리 할당 (에러 방지)
            data_dict[key] = {} 
    
    return data_dict


def validate_data(data_dict):
    # 필수 데이터프레임 확인
    required = ['df_issue', 'df_pr', 'df_fork']
    for key in required:
        if key not in data_dict or data_dict[key] is None or data_dict[key].empty:
            return False, f"데이터 {key}가 비어있거나 로드되지 않았습니다."
    return True, "성공"

def service_load_data_from_disk(SAVE_DIR='data/model'):
    data_dict = {}
    
    # 디렉토리가 존재하는지 확인
    if not os.path.exists(SAVE_DIR):
        st.error(f"경로를 찾을 수 없습니다: {SAVE_DIR}")
        return data_dict

    # 폴더 내 모든 파일 리스트 가져오기
    files = os.listdir(SAVE_DIR)
    
    # 1. Parquet 파일 처리
    for file in files:
        if file.endswith('.parquet'):
            key = file.replace('.parquet', '')
            path = os.path.join(SAVE_DIR, file)
            data_dict[key] = pd.read_parquet(path)
            
    # 2. JSON 파일 처리
    for file in files:
        if file.endswith('.json'):
            key = file.replace('.json', '')
            path = os.path.join(SAVE_DIR, file)
            with open(path, 'r', encoding='utf-8') as f:
                data_dict[key] = json.load(f)
    
    return data_dict
def predict_with_real_titles(new_texts, cluster_mapping, threshold=0.40):
    pca = joblib.load('trained_pca.pkl')
    scaler = joblib.load('trained_scaler.pkl')
    gmm = joblib.load('trained_gmm.pkl')
    model_sbert = get_sbert_model()
    
    # 1. 인코딩 및 전처리
    embeddings = model_sbert.encode(new_texts, show_progress_bar=False)
    reduced_embeddings = pca.transform(embeddings)
    scaled_embeddings = scaler.transform(reduced_embeddings)
    
    # 2. GMM 예측 및 최댓값 추출
    probs = gmm.predict_proba(scaled_embeddings)
    max_probs = np.max(probs, axis=1)
    pred_clusters = np.argmax(probs, axis=1)
    
    # 3. Threshold 기준 미달이면 -1(기타) 처리
    final_clusters = []
    for cluster, max_prob in zip(pred_clusters, max_probs):
        if max_prob < threshold:
            final_clusters.append(-1)
        else:
            final_clusters.append(cluster)
            
    # 4. 결과 데이터프레임 생성
    result_df = pd.DataFrame({
        'Text': new_texts,
        'Cluster_Num': final_clusters,
        'Confidence': max_probs
    })
    
    # ================= [이 부분이 핵심입니다] =================
    # 미리 준비한 딕셔너리를 이용해 숫자 번호를 실제 제목으로 치환합니다.
    result_df['Theme_Title'] = result_df['Cluster_Num'].map(cluster_mapping)
    # =========================================================
    
    return result_df