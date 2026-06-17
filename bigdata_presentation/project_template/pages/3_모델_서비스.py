import streamlit as st
import pandas as pd
import numpy as np
import joblib
import json
import shutil
import os
from sentence_transformers import SentenceTransformer
from huggingface_hub import snapshot_download
# ----------------------------------------------------
# [설정 및 캐싱] 모델을 한 번만 로드하여 서비스 속도를 극대화합니다.
# ----------------------------------------------------
@st.cache_resource
def load_sbert_model():
    # 다국어 지원 SBERT 모델 로드
    return SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2' , use_auth_token=False)

@st.cache_data
def load_cluster_mapping(type):  # 👈 여기에 type 인자를 받을 수 있게 추가!
    # 유저가 선택한 타입에 따라 불러올 파일명을 동적으로 결정합니다.
    if type == "issue":
        json_path = 'bigdata_presentation\project_template\data\model\issue_labels.json'
    else:
        json_path = 'bigdata_presentation\project_template\data\model\pr_labels.json'  # 👈 깃허브 PR용 레이블 JSON 파일명
    
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        mapping = {int(k): v for k, v in json_data.items()}
    else:
        st.sidebar.error(f"❌ {json_path} 파일을 찾을 수 없습니다. 기본 텍스트로 대체합니다.")
        mapping = {i: f"{type.upper()} 테마 {i}" for i in range(10)}
        
    mapping[-1] = "기타 (분류 불가)"
    return mapping

# ----------------------------------------------------
# [핵심 로직] 예측 함수 정의
# ----------------------------------------------------
def predict_with_real_titles(new_texts, event_type, cluster_mapping, threshold=0.40, score_threshold=-35):
    # 유저가 에러 났던 경로 패턴을 기반으로 모델 로드
    base_dir = rf'bigdata_presentation\project_template\data\pred\{event_type}'
    
    try:
        pca = joblib.load(os.path.join(base_dir, 'trained_pca.pkl'))
        scaler = joblib.load(os.path.join(base_dir, 'trained_scaler.pkl'))
        gmm = joblib.load(os.path.join(base_dir, 'trained_gmm.pkl'))
    except FileNotFoundError:
        os.makedirs(base_path, exist_ok=True)
        st.error(f"❌ '{event_type}'에 대한 학습된 모델 파일(.pkl)을 찾을 수 없습니다. 먼저 학습을 진행해주세요.")
        return None

    # SBERT 임베딩 (캐싱된 모델 사용)
    model_sbert = load_sbert_model()
    embeddings = model_sbert.encode(new_texts, show_progress_bar=False)
    
    # 전처리 및 GMM 예측
    reduced_embeddings = pca.transform(embeddings)
    scaled_embeddings = scaler.transform(reduced_embeddings)
    probs = gmm.predict_proba(scaled_embeddings)
    
    max_probs = np.max(probs, axis=1)
    pred_clusters = np.argmax(probs, axis=1)
    
    # ------------------------------------------------------------------
    # 🔥 [추가 1] GMM 절대 밀도 점수(score_samples) 계산 로직 삽입
    # ------------------------------------------------------------------
    scores = gmm.score_samples(scaled_embeddings)
    
    # ------------------------------------------------------------------
    # 🔥 [추가 2] 왜 '기타'로 빠지는지 원인을 눈으로 확인하는 디버깅 시각화
    # ------------------------------------------------------------------
    st.write("--- 🛠️ AI 내부 예측 점수 실시간 디버깅 ---")
    st.write(f"• 상대 확률(Confidence): `{max_probs[0]:.4f}` (설정한 커트라인: {threshold})")
    st.write(f"• 절대 밀도 점수(Score): `{scores[0]:.4f}` (설정한 커트라인: {score_threshold})")
    st.write("--------------------------------------------------")
    
    # ------------------------------------------------------------------
    # 🔥 [수정 3] 확률과 절대 점수 커트라인을 둘 다 통과해야 번호를 부여하도록 변경
    # ------------------------------------------------------------------
    final_clusters = []
    for cluster, prob, score in zip(pred_clusters, max_probs, scores):
        # 확률이 기준보다 낮거나, '절대 밀도 점수'가 기준보다 낮으면 무조건 -1(기타) 처리
        if prob < threshold or score < score_threshold:
            final_clusters.append(-1)
        else:
            final_clusters.append(cluster)
        
    # ------------------------------------------------------------------
    # 🔥 [추가 4] 웹 대시보드 화면에서 꺼내 쓸 수 있도록 Score도 데이터프레임에 박아줌
    # ------------------------------------------------------------------
    result_df = pd.DataFrame({
        'Text': new_texts,
        'Cluster_Num': final_clusters,
        'Confidence': max_probs,
        'Score': scores  
    })
    
    # 실제 제목 매핑
    result_df['Theme_Title'] = result_df['Cluster_Num'].map(cluster_mapping)
    return result_df

# 메인 타이틀 (상단 고정)
st.title("🤖 AI 깃허브 데이터 테마 분류 서비스")
st.write("학습된 GMM 모델을 바탕으로 새로운 이슈(Issue)나 PR(Pull Request) 문장의 테마를 실시간 예측합니다.")

# 변수 초기화
pca_issue, scaler_issue, gmm_issue = None, None, None
pca_pull, scaler_pull, gmm_pull = None, None, None

# ----------------------------------------------------
# 1. Issue 모델 로드 및 설정 Section
# ----------------------------------------------------
st.subheader("📊 Issue 모델 설정")
base_dir_issue = r'bigdata_presentation\project_template\data\pred\issue'

pca_path_issue = os.path.join(base_dir_issue, 'trained_pca.pkl')
scaler_path_issue = os.path.join(base_dir_issue, 'trained_scaler.pkl')
gmm_path_issue = os.path.join(base_dir_issue, 'trained_gmm.pkl')

if os.path.exists(pca_path_issue) and os.path.exists(scaler_path_issue) and os.path.exists(gmm_path_issue):
    try:
        pca_issue = joblib.load(pca_path_issue)
        scaler_issue = joblib.load(scaler_path_issue)
        gmm_issue = joblib.load(gmm_path_issue)
        st.success("✅ issue 로컬 모델 로드 완료!")
        
        # [추가] 모델이 존재할 때 삭제할 수 있는 버튼 제공
        if st.button("🗑️ issue 모델 삭제하기", key="del_issue"):
            if os.path.exists(base_dir_issue):
                shutil.rmtree(base_dir_issue)
            st.warning("🗑️ issue 모델 폴더를 삭제했습니다.")
            st.rerun()
            
    except Exception as e:
        st.error(f"❌ Issue 모델 로드 실패: {e}")
else:
    st.warning(f"⚠️ issue 모델 폴더가 지정된 경로({base_dir_issue})에 없습니다.")
    source_dir_issue = st.text_input("이동할 issue 원본 폴더의 전체 경로를 입력하세요:", placeholder=r"예: C:\Users\User\Downloads\issue", key="path_issue")
    
    if st.button("issue 폴더 통째로 복사하기", key="btn_issue"):
        if source_dir_issue and os.path.exists(source_dir_issue):
            if os.path.exists(base_dir_issue):
                shutil.rmtree(base_dir_issue)
            shutil.copytree(source_dir_issue, base_dir_issue)
            st.success("🎉 issue 폴더 이동 완료!")
            st.rerun()
        else:
            st.error("❌ 올바른 경로를 입력해주세요.")

st.markdown("---") # 구분선

# ----------------------------------------------------
# 2. Pull 모델 로드 및 설정 Section
# ----------------------------------------------------
st.subheader("📊 Pull 모델 설정")
base_dir_pull = r'bigdata_presentation\project_template\data\pred\pull'

pca_path_pull = os.path.join(base_dir_pull, 'trained_pca.pkl')
scaler_path_pull = os.path.join(base_dir_pull, 'trained_scaler.pkl')
gmm_path_pull = os.path.join(base_dir_pull, 'trained_gmm.pkl')

if os.path.exists(pca_path_pull) and os.path.exists(scaler_path_pull) and os.path.exists(gmm_path_pull):
    try:
        pca_pull = joblib.load(pca_path_pull)
        scaler_pull = joblib.load(scaler_path_pull)
        gmm_pull = joblib.load(gmm_path_pull)
        st.success("✅ pull 로컬 모델 로드 완료!")
        
        # [추가] 모델이 존재할 때 삭제할 수 있는 버튼 제공
        if st.button("🗑️ pull 모델 삭제하기", key="del_pull"):
            if os.path.exists(base_dir_pull):
                shutil.rmtree(base_dir_pull)
            st.warning("🗑️ pull 모델 폴더를 삭제했습니다.")
            st.rerun()
            
    except Exception as e:
        st.error(f"❌ Pull 모델 로드 실패: {e}")
else:
    st.warning(f"⚠️ pull 모델 폴더가 지정된 경로({base_dir_pull})에 없습니다.")
    source_dir_pull = st.text_input("이동할 pull 원본 폴더의 전체 경로를 입력하세요:", placeholder=r"예: C:\Users\User\Downloads\pull", key="path_pull")
    
    if st.button("pull 폴더 통째로 복사하기", key="btn_pull"):
        if source_dir_pull and os.path.exists(source_dir_pull):
            if os.path.exists(base_dir_pull):
                shutil.rmtree(base_dir_pull)
            shutil.copytree(source_dir_pull, base_dir_pull)
            st.success("🎉 pull 폴더 이동 완료!")
            st.rerun()
        else:
            st.error("❌ 올바른 경로를 입력해주세요.")

st.markdown("---") # 구분선


if pca_issue and scaler_issue and gmm_issue and pca_pull and scaler_pull and gmm_pull:
    
    # ----------------------------------------------------
    # [UI 레이아웃] Streamlit 화면 구성
    # ----------------------------------------------------
    st.set_page_config(page_title="AI 텍스트 테마 분류 서비스", layout="wide")

    st.title("🤖 AI 깃허브 데이터 테마 분류 서비스")
    st.markdown("학습된 GMM 모델을 바탕으로 새로운 이슈(Issue)나 PR(Pull Request) 문장의 테마를 실시간 예측합니다.")

    # 사이드바 컨트롤러
    st.sidebar.header("🎛️ 서비스 설정")
    event_type = st.sidebar.selectbox("분석할 이벤트 유형 선택", ["issue", "pull"])
    threshold = st.sidebar.slider("분류 인정 최소 확률 (Threshold)", 0.0, 1.0, 0.40, 0.05)
    score_threshold = st.sidebar.number_input(
        "절대 밀도 커트라인 (Score Threshold)", 
        min_value=-500,  # 직접 입력할 수 있도록 최소 범위를 -500으로 넉넉하게 확장
        max_value=0,     # 최대 밀도 점수는 0
        value= -140,       # 기본값은 -45 지정
        step=1,          # 화살표 버튼을 누를 때 1씩 증감
        help="숫자를 마이너스 방향으로 더 크게 적을수록(예: -60, -80) 분류 기준이 느슨해집니다."
    )

    st.sidebar.markdown("---")
    st.sidebar.info("💡 **Tip:** 확률이 이 기준보다 낮으면 자동으로 '기타 (분류 불가)' 그룹으로 지정됩니다.")

    # 데이터 준비
    if event_type == "issue":
        cluster_mapping = load_cluster_mapping(type="issue")
    else:
        cluster_mapping = load_cluster_mapping(type="pr")


    # 메인 화면 탭 구성
    tab1, tab2 = st.tabs(["✍️ 한 줄 텍스트 예측", "📁 파일(CSV/Excel) 대량 예측"])

    with tab1:
        st.subheader("실시간 문장 분석")
        user_input = st.text_area("분석하고 싶은 댓글이나 본문 내용을 입력하세요:", 
                                placeholder="예: 주말 카페 알바 구인 공고 올렸습니다. 확인 부탁드립니다.")
        
        if st.button("🚀 테마 예측하기", key="single_pred"):
            if user_input.strip() == "":
                st.warning("텍스트를 입력해주세요.")
            else:
                with st.spinner("AI가 분석 중입니다..."):
                    res = predict_with_real_titles([user_input], event_type, cluster_mapping, threshold,  score_threshold=score_threshold)
                    
                    if res is not None:
                        row = res.iloc[0]
                        st.success("분석 완료!")
                        
                        # 카드 형태로 결과 강조
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric(label="예측된 테마 주제", value=row['Theme_Title'])
                        with col2:
                            st.metric(label="분류 신뢰도 (확률)", value=f"{row['Confidence']*100:.1f}%")

    with tab2:
        st.subheader("데이터 파일 업로드 분석")
        uploaded_file = st.file_uploader("CSV 또는 엑셀 파일을 업로드 하세요.", type=["csv", "xlsx"])
        
        if uploaded_file is not None:
            # 파일 읽기
            if uploaded_file.name.endswith('.csv'):
                df_upload = pd.read_csv(uploaded_file)
            else:
                df_upload = pd.read_excel(uploaded_file)
                
            st.write("📋 업로드된 데이터 미리보기 (상위 5개)")
            st.dataframe(df_upload.head())
            
            # 텍스트가 들어있는 컬럼 선택 유도
            text_column = st.selectbox("텍스트 분석을 진행할 컬럼을 선택하세요:", df_upload.columns)
            
            if st.button("📊 대량 데이터 분류 시작", key="batch_pred"):
                text_list = df_upload[text_column].fillna("").astype(str).tolist()
                
                with st.spinner(f"{len(text_list)}건의 데이터를 AI 모델로 분류 중..."):
                    res_df = predict_with_real_titles(text_list, event_type, cluster_mapping, threshold , score_threshold=score_threshold)
                    
                    if res_df is not None:
                        # 기존 업로드 데이터에 결과 붙이기
                        df_upload['분류_테마'] = res_df['Theme_Title'].values
                        df_upload['분류_확률'] = res_df['Confidence'].values
                        
                        st.success("🎯 대량 분류가 완료되었습니다!")
                        
                        # 통계 및 시각화 리포트
                        st.subheader("📊 분류 결과 요약")
                        theme_counts = df_upload['분류_테마'].value_counts()
                        st.bar_chart(theme_counts)
                        
                        # 결과 데이터 테이블
                        st.subheader("🔍 전체 결과 데이터 확인")
                        st.dataframe(df_upload)
                        
                        # 다운로드 버튼 제공
                        csv = df_upload.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                        st.download_button(
                            label="📥 분류 결과 다운로드 (CSV)",
                            data=csv,
                            file_name=f"classified_{event_type}_results.csv",
                            mime="text/csv"
                        )