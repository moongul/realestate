from opencode_helper import OpenCodeHelper
import json

raw_response = """```json
{
    "market_vibe": "전세 매물 급감 및 월세 전환 가속화로 임대차 시장 구조적 변화 진행 중",
    "key_factors": "1년 새 전세 매물 35% 급감, 수도권 월세 비중 70% 초과, 전세가 추가 상승 전망(KB 부동산 보고서)",
    "attention_level": "주의 (전세 수요자 매물 확보 난항, 월세 전환 불가피 국면)",
    "regional_data": [
        {
            "region": "수도권",
            "trend": "월세 중심으로 임대차 시장 재편 진행",
            "price_info": "월세 비중 70% 초과",
            "note": "KB부동산 보고서 기준, 전세→월세 전환율 임계점 돌파"
        },
        {
            "region": "전국(임대차 시장 전반)",
            "trend": "전세 매물 1년 새 35% 급감, 공급 부족 심화",
            "price_info": "전세 매물 전년 대비 35% 감소",
            "note": "매물 감소 원인 및 지속 여부 불확실, '파격 전망' 언급"
        }
    ],
    "expert_insight": "전세 매물이 1년 새 35% 급감하고 수도권 월세 비중이 70%를 넘어서면서 전세 중심의 임대차 시장이 사실상 해체 수순에 접어들었다. 실수요자는 전세 대기 전략보다 월세 수용 또는 매매 전환을 적극 검토할 시점이며, 전세가 추가 상승이 예상되는 만큼 계약 갱신 시점 관리가 중요하다."
}
```"""

parsed = OpenCodeHelper.parse_json(raw_response)
print(f"Parsed Type: {type(parsed)}")
print(f"Parsed Value: {parsed}")
if not parsed:
    print("Parsed data evaluates to False!")
else:
    print("Parsed data evaluates to True!")
