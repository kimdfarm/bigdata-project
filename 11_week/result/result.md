1. PROMPT_TEMPLATE = """당신은 웹입니다. 각 HTTP 요청을 받았는데 지나가는 요청은 "Normal" 만약 정상적인 요청이 아닌 정보를 얻거나 오류나는 요청이 추가로 이루어져 있다면 "Anomalous"으로 분류하고 간략한 이유를 제공하십시오.\n\n예시:\n요청: GET /index.jsp HTTP/1.1\n출력: {{"label": "Normal", "reason": "표준 페이지 요청, 의심스러운 패턴 없음"}}\n\n요청: GET /search?q=\' OR \'1\'=\'1 HTTP/1.1\n출력: {{"label": "Anomalous", "reason": "오류 원인"}}\n\n다음 요청을 분류하십시오.\n요청: {http_text}
\nOutput:"""
- LLM 정확도: 0.8500
- LLM F1:    0.8598
- 분류 실패(Unknown): 1건

|               |precision  |  recall  |f1-score |  support|
| :--- | :---: | :---: | :---: | ---: |
 |     Normal  |     0.85   |   0.83  |    0.84   |     47|
  | Anomalous    |   0.85    |  0.87   |   0.86   |     53|
 |   accuracy   |           |          |   0.85   |    100|
  | macro avg    |   0.85    |  0.85   |   0.85   |    100|
|weighted avg    |   0.85    |  0.85    |  0.85  |     100|

2. PROMPT_TEMPLATE = """당신은 인테넷입니다 클라이언트가 요청을 보냈습니다. 요청이 오류를 이르키거나 sql 언어를 쓰어서 정보를 얻을러는 목적이 있다면  "Anomalous" 만약 정상적인 요청이라면 "Normal"으로 분류하고 간략한 이유를 제공하십시오.\n\n예시:\n요청: GET /index.jsp HTTP/1.1\n출력: {{"label": "Normal", "reason": "표준 페이지 요청, 의심스러운 패턴 없음"}}\n\n요청: GET /search?q=\' OR \'1\'=\'1 HTTP/1.1\n출력: {{"label": "Anomalous", "reason": "오류 원인"}}\n\n다음 요청을 분류하십시오.\n요청: {http_text}
\nOutput:"""

- LLM 정확도: 0.8100
- LLM F1:    0.7957
- 분류 실패(Unknown): 1건

 |            | precision  |  recall | f1-score |  support|
 | :--- | :---: | :---: | :---: | ---: |
 |     Normal    |   0.73   |   0.94  |    0.82   |     47|
 |  Anomalous    |   0.93  |    0.70   |   0.80   |     53|
|   accuracy    |          |         |    0.81    |   100|
 |  macro avg    |   0.83   |   0.82   |   0.81   |    100|
|weighted avg    |   0.83  |    0.81   |   0.81     |  100|


3. PROMPT_TEMPLATE = """당신은 사이버 보안수사대입니다. 각 HTTP 요청을 의뢰 받았는데 https 형태가 정상이면 "Normal" 만약 수사경력 바탕으로 비정상인게 확실하다면 "Anomalous"으로 분류하고 간략한 이유를 제공하십시오.
\n\n예시:\n요청: GET /index.jsp HTTP/1.1\n출력: {{"label": "Normal", "reason": "표준 페이지 요청, 의심스러운 패턴 없음"}}\n\n요청: GET /search?q=\' OR \'1\'=\'1 HTTP/1.1\n출력: {{"label": "Anomalous", "reason": "오류 원인"}}\n\n다음 요청을 분류하십시오.\n요청: {http_text}
\nOutput:"""

- LLM 정확도: 0.8600
- LLM F1:    0.8727
- 분류 실패(Unknown): 0건

 |            | precision  |  recall | f1-score  | support|
| :--- | :---: | :---: | :---: | ---: |
 |     Normal   |    0.88  |    0.81  |    0.84   |     47|
 |  Anomalous    |   0.84   |   0.91  |    0.87    |    53|

 |   accuracy   |           |         |    0.86    |   100|
  | macro avg   |    0.86   |   0.86  |    0.86    |   100|
|weighted avg   |    0.86    |  0.86   |   0.86  |     100|


4. PROMPT_TEMPLATE = """당신은 해커입니다. 각 HTTP 요청은 당신이 서버를 접속한 기록입니다. 만약 당신이 접속 목적이 일반 사람과 똑같은 접속이라면  "Normal" 당신이 서버를 오류 이르키거나 정보 얻을러는 특수 목적으로 각 HTTP 요청을 요청했다면 "Anomalous"으로 분류하고 간략한 이유를 제공하십시오.
\n\n예시:\n요청: GET /index.jsp HTTP/1.1\n출력: {{"label": "Normal", "reason": "표준 페이지 요청, 의심스러운 패턴 없음"}}\n\n요청: GET /search?q=\' OR \'1\'=\'1 HTTP/1.1\n출력: {{"label": "Anomalous", "reason": "오류 원인"}}\n\n다음 요청을 분류하십시오.\n요청: {http_text}
\nOutput:"""

- LLM 정확도: 0.8800
- LLM F1:    0.8929
- 분류 실패(Unknown): 0건

 |           |  precision  |  recall|  f1-score  | support|
| :--- | :---: | :---: | :---: | ---: |
 |     Normal     |  0.93   |   0.81    |  0.86    |    47|
  | Anomalous    |   0.85   |   0.94   |   0.89   |     53|

 |   accuracy    |          |         |    0.88  |     100|
 |  macro avg    |   0.89    |  0.88   |   0.88   |    100|
|weighted avg    |   0.88    |  0.88   |   0.88   |    100|


5. PROMPT_TEMPLATE = """당신은 일확천금을 얻을 기회가 찾아왔습니다. 각 HTTP 요청을 정확하게 알아첸다면 1000조을 얻을 수 있고 엄청난 영광을 누릴 수 있습니다.  당신은 http의 요청들을 어떻게 해서든 알아내면 됩니다 정보들을 봐도 되고 해커나 정보 요원의 경력을 써도 되고 심지여 서버가 직접 당신에게 이런 http 요청이 어떤 결과를 가져오는지 알 수 있습니다. 이 정보들을 바탕으로 각 HTTP 요청이 정상이라면 "Normal" 각 HTTP 요청이 비정상이라면  "Anomalous"으로 분류하고 간략한 이유를 제공하십시오.
\n\n예시:\n요청: GET /index.jsp HTTP/1.1\n출력: {{"label": "Normal", "reason": "표준 페이지 요청, 의심스러운 패턴 없음"}}\n\n요청: GET /search?q=\' OR \'1\'=\'1 HTTP/1.1\n출력: {{"label": "Anomalous", "reason": "오류 원인"}}\n\n다음 요청을 분류하십시오.\n요청: {http_text}
\nOutput:"""

- LLM 정확도: 0.8700
- LLM F1:    0.8807
- 분류 실패(Unknown): 0건

  |            |precision  |  recall | f1-score  | support|
| :--- | :---: | :---: | :---: | ---: |
    |  Normal  |     0.89    |  0.83  |    0.86    |    47|
   |Anomalous   |    0.86   |   0.91   |   0.88   |     53|
  |  accuracy     |         |          |   0.87   |    100|
 |  macro avg   |    0.87   |   0.87   |   0.87    |   100|
|weighted avg    |   0.87   |   0.87   |   0.87  |     100|