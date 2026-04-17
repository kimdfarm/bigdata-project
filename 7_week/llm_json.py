import ollama
import json

reviews = [
    "배송은 느린데! 재구매 의사 있습니다.",
    "불량품이 왔는데 교환도 해주네요. 최고입니다.",
    "가격은 저렴한데 품질은 보통이에요."
]

results = []
for r in reviews:
    response = ollama.chat(
        model="gemma3:4b",
        messages=[
            {"role":"system","content":"""당신은 리뷰 분석 전문가입니다,
            주어진 리뷰를 분석하여 반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트는 포함하지 마세요 
            {"s":"긍정/부정/중립" , "cfd":0.0~1.0 , "kwd":["키워드 1" ,"키워드 2"]}"""
            },
            {"role":"user","content":r}])
    raw = response["message"]["content"]

try:
    c = raw.strip()
    if "```json" in c:
        c = c.split("```json")[1].split("```")[0].strip()
    elif "```" in c:
        c = c.split("```")[1].split("```")[0].strip()
    data = json.loads(c)
    results.append(data)
    print(f"리뷰: {r[:25]}...")
    print(f"   감성: {data['s']}, 확신도: {data['cfd']}")
    print(f"   키워드: {data['kwd']}")
except json.JSONDecodeError:
    print(f"JSON 파싱 실패: {raw[:100]}")

print("-" * 50)

print(f"\n총 {len(results)}개 리뷰 분석 완료")


            

