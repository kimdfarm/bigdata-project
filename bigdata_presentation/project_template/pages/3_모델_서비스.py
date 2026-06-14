# pages/3_모델_서비스.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# 💡 Ollama 연동을 위한 라이브러리 (터미널에 pip install ollama 필요)
try:
    import ollama
except ImportError:
    os.system("pip install ollama")
    import ollama

# 한글 깨짐 방지
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

st.title("🤖 ML & Ollama LLM 기반 GitHub 환경 진단 및 맞춤형 프롬프트 서비스")
st.write("K-Means로 프로젝트 환경 유형을 분류하고, **Ollama 로컬 LLM 프롬프트**를 통해 맞춤형 운영 전략 리포트를 생성합니다.")

# 데이터 경로 및 가상 ML 데이터 빌드 (기존 로직 유지)
base_path = r"C:\_proj\bigdata-project\bigdata-project\bigdata_presentation\project_template\data"

@st.cache_data
def build_mock_ml_data():
    np.random.seed(42)
    type1 = np.random.exponential(scale=80, size=(100, 3)) + [50, 40, 10]
    type2 = np.random.exponential(scale=40, size=(100, 3)) + [10, 20, 80]
    type3 = np.random.gamma(shape=2, scale=5, size=(100, 3))
    data = np.vstack([type1, type2, type3])
    df_ml = pd.DataFrame(data, columns=['Fork수', 'PR수', 'Issue수'])
    df_ml = df_ml.clip(lower=0).round().astype(int)
    labels = ['개발 기여 중심형 환경'] * 100 + ['소통 커뮤니티형 환경'] * 100 + ['초기 및 정체형 환경'] * 100
    df_ml['환경 유형'] = labels
    return df_ml

df_model_data = build_mock_ml_data()

# ----------------- 1. AI 생태계 시각화 -----------------
st.markdown("---")
st.subheader("📊 1. AI가 분석한 현재 GitHub 생태계 환경 구조")
fig, ax = plt.subplots(figsize=(10, 3.5))
sns.scatterplot(data=df_model_data, x='Fork수', y='PR수', hue='환경 유형', palette='Set2', alpha=0.8, ax=ax)
ax.set_title("GitHub 프로젝트 행동 패턴 군집 분포도")
st.pyplot(fig)

# ----------------- 2. 진단 및 Ollama 프롬프트 생성 서비스 -----------------
st.markdown("---")
st.subheader("🔮 2. 나의 GitHub 프로젝트 환경 성향 진단 & LLM 전략 제언")
st.write("레포지토리의 협업 지표를 입력하면, ML 모델의 분류 결과와 지표 데이터를 **Ollama**에게 전달하여 맞춤형 컨설팅을 받습니다.")

# Ollama 모델 선택 사이드바 (기본적으로 가장 가벼운 llama3나 llama2, gemma, qwen 등을 PC에 설치해 두셔야 합니다)
st.sidebar.markdown("### 🦙 Ollama 설정")
ollama_model = st.sidebar.text_input("사용할 Ollama 모델명 입력", value="gemma2:2b") # 또는 llama3, qwen2.5 등
st.sidebar.caption("※ 로컬 PC 터미널에서 `ollama run 모델명`으로 모델이 먼저 다운로드되어 있어야 작동합니다.")

col1, col2, col3 = st.columns(3)
with col1:
    user_fork = st.number_input("⏳ 예상/현재 Fork 수", min_value=0, max_value=500, value=30)
with col2:
    user_pr = st.number_input("🚀 예상/현재 Pull Request 수", min_value=0, max_value=500, value=25)
with col3:
    user_issue = st.number_input("💬 예상/현재 Issue 수", min_value=0, max_value=500, value=60)

if st.button("🚀 ML 분류 및 Ollama 프롬프트 분석 시작"):
    
    # [단계 1] K-Means 기반 간단한 거리 예측 수행
    center_heavy = np.array([130, 120, 30])
    center_comm = np.array([50, 60, 120])
    center_rare = np.array([10, 10, 10])
    user_vec = np.array([user_fork, user_pr, user_issue])
    
    dist_heavy = np.linalg.norm(user_vec - center_heavy)
    dist_comm = np.linalg.norm(user_vec - center_comm)
    dist_rare = np.linalg.norm(user_vec - center_rare)
    min_dist = min(dist_heavy, dist_comm, dist_rare)
    
    if min_dist == dist_heavy:
        ml_result = "개발 기여 중심형 환경"
    elif min_dist == dist_comm:
        ml_result = "소통 커뮤니티형 환경"
    else:
        ml_result = "초기 및 정체형 환경"
        
    st.success(f"🎯 [ML 결과] 이 프로젝트는 **'{ml_result}'** 군집에 해당합니다.")
    
    # [단계 2] Ollama 전용 페이로드 및 프롬프트 엔지니어링 설계
    st.markdown("---")
    st.subheader("📑 3. Ollama가 생성한 오픈소스 환경 컨설팅 리포트")
    
    # 💡 Ollama에게 주입할 핵심 프롬프트 구성 (System & User Prompt 구조)
    prompt_message = f"""
    당신은 전 세계 오픈소스 생태계를 분석하는 대한민국 최고의 GitHub 데이터 분석 전문가이자 컨설턴트입니다.
    데이터 수치를 기반으로 이 프로젝트가 처한 GitHub 환경을 분석하고 앞으로의 구체적인 개선 전략을 제공해야 합니다.

    [현재 프로젝트 데이터]
    - 머신러닝 군집 분류 결과: {ml_result}
    - 현재까지 발생한 Fork 수: {user_fork}개
    - 등록된 Pull Request(PR) 수: {user_pr}개
    - 제기된 Issue 수: {user_issue}개

    [보고서 작성 가이드라인]
    1. 이 프로젝트의 현재 협업 환경 패턴(지표적 특성)을 날카롭게 요약해 주세요.
    2. 머신러닝 결과인 '{ml_result}'에 맞는 최적의 레포지토리 활성화 전략을 2가지 제시해 주세요.
    3. 친절하고 전문적인 한국어로 답변해 주세요.
    """
    
    # 스트리밍 실시간 답변 출력을 위한 Streamlit UI 적용
    with st.spinner("로컬 Ollama LLM 모델이 프롬프트를 해석하여 맞춤형 리포트를 작성 중입니다..."):
        try:
            # Ollama API 호출
            response = ollama.chat(
                model=ollama_model,
                messages=[
                    {"role": "user", "content": prompt_message}
                ]
            )
            
            # 결과 텍스트 출력
            analysis_text = response['message']['content']
            st.markdown(analysis_text)
            st.balloons()
            
        except Exception as e:
            st.error("⚠️ Ollama 연동에 실패했습니다. 다음 사항을 확인하세요:")
            st.write(f"1. 컴퓨터 백그라운드에 Ollama 앱이 켜져 있나요?")
            st.write(f"2. 터미널에 `ollama pull {ollama_model}` 명령어로 해당 모델을 다운로드 받아 두셨나요?")
            st.write(f"**오류 내용:** {e}")