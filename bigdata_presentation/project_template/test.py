import pandas as pd
# 1. 모든 열이 다 보이도록 설정 (기본값은 보통 20)
pd.set_option('display.max_columns', None)

# 2. 열 너비를 제한 없이 늘리기 (글자가 잘리지 않음)
pd.set_option('display.max_colwidth', None)

# 3. 모든 행을 다 보고 싶은 경우 (데이터가 너무 많으면 주의)
pd.set_option('display.max_rows', None)

# 4. 터미널 가로 너비 제한 해제 (가로로 길게 출력)
pd.set_option('display.width', 1000)
df = pd.read_csv(r"bigdata_presentation\project_template\data\use\sampled_IssuesEvent.csv")
dfs = df.sample(100)
print(df.sample(20))
dfs.to_csv("issue100testsample.csv")