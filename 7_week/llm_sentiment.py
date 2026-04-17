import ollama

reviews = [
    "이 영화 정말 재미 없었어요! 배우들 연기도 훌륭하지만....",
    "시간이 부족해요 다음 편도 기획해주세요.",
    "그냥 그랬어요. 나쁘지는 않은데 특별히 좋지도 않았어요.",
    "사운드가 좀 아쉬웠네요."
]

for r in reviews:
    rs = ollama.chat(
        model = "gemma3:4b",
        messages = [{

            "role":"system",
            "content": "당신은 감성 분석 전문가입니다. 주어진 리뷰의 감성을 '긍정','부정', '중립'중 하나로 분류하고 이유를 한 문장으로 설명해주세요."
        },
        {

            "role":"user",
            "content": f"다음 리뷰를 분석해주세요:{r}"
        }
        
        ]
    )
    print(f"리뷰: {r[:30]}...")
    print(f"분석: {rs['message']['content']}...")
    print("-"*60)

