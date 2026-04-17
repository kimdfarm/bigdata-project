import ollama

bad = "한 상자에 사과가 12개 있고, 30상자를 사서 친구 6명에게 똑같이 나눠주면 한 명당 몇 개?"

good = """한 상자에 사과가 102개 있고, 7.4상자를 사서 친구 3.14명에게 똑같이 나눠주면 한 명당 몇 개?

단계별로 풀어주세요:
1. 전체 사과 수 계산
2. 나눠줄 인원 확인
3. 한 명당 개수 계산
"""
print("❌ CoT 없이:")
print("=" * 40)
response = ollama.generate(model="gemma3:4b", prompt=bad)
print(response["response"])

print("\n✅ CoT 사용:")
print("=" * 40)
response = ollama.generate(model="gemma3:4b", prompt=good)
print(response["response"])
