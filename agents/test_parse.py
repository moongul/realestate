from opencode_helper import OpenCodeHelper
import json

raw = """```json
{
    "market_vibe": "AI 프롭테크 붐 및 디지털 전환 가속화",
    "key_factors": "네이버 '온서비스 AI' 부동산·증권 분야 전면 확장, 땅집고 AI 경매 플랫폼 '땅집봇' 토스 미니앱 론칭, 땅집고의 AI프롭테크 기업 트랜스 파머 지분 투자",
    "attention_level": "관심",
    "regional_data": [
        {"region": "전국 (온라인 플랫폼)", "trend": "AI 기반 부동산 정보·경매 서비스 확대", "price_info": "언급된 구체적 시세 없음", "note": "네이버, 땅집고 등 포털·부동산 미디어의 AI 서비스 경쟁 본격화"}
    ],
    "expert_insight": "AI가 부동산 투자 의사결정 보조 도구로 본격 진입하며, 경매·공매 분야에서는 전용 AI 모델이 범용 AI(ChatGPT, Gemini)보다 우위를 점하고 있음. 투자자는 AI 플랫폼의 정보 비대칭 해소 효과를 활용할 수 있으나, 최종 판단은 여전히 인간의 검증이 필요함."
}
```"""

print("--- Testing parse_json ---")
res = OpenCodeHelper.parse_json(raw)
print(f"Result: {res}")
print(f"Is falsey? {not res}")
