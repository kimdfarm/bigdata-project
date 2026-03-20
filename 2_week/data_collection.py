import requests 
import pandas as pd 
import json 
import os 
from dotenv import load_dotenv, find_dotenv 
# ============================================================
 # 1. API 설정
# ============================================================
 # .env 파일에서 API 키 로드 
load_dotenv(find_dotenv()) 
API_KEY = os.getenv("API_KEY") 
# 에어코리아 대기오염정보 - 시도별 실시간 측정정보 조회 
url = "https://openapi.gg.go.kr/AtmosMeasureVicariousExecut" 

 # ============================================================
 # 2. 요청 파라미터 설정
# ============================================================ 
params = { 
"serviceKey": API_KEY,       
# 인증키 
"returnType": "json",        
"numOfRows": "100",          
"pageNo": "1",               
"sidoName": "서울",           
"ver": "1.0"                 
} 
# 응답 형식 (json 또는 xml) 
# 한 페이지에 가져올 데이터 수 
# 페이지 번호 
# 시도 이름 (서울, 부산, 대구, 인천 등) 
# API 버전 
# ============================================================
 # 3. API 호출
# ============================================================ 
print("▶ API 호출 중...") 
response = requests.get(url) 
# 응답 상태 확인 
print(f"▶ 응답 상태 코드: {response.status_code}") 
# 1. 상태 코드 확인 (200이 아니면 문제가 있는 것)
print(f"상태 코드: {response.status_code}")

# 2. 실제 들어온 텍스트 내용 확인 (이게 핵심!)
print(f"응답 내용: {response.text}")

# 3. 데이터가 있을 때만 JSON으로 변환
if response.status_code == 200 and response.text.strip():
    data = response.json()
else:
    print("JSON을 파싱할 수 없는 응답입니다.")