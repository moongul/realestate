import os
import json
from google import genai
from dotenv import load_dotenv
from db_manager import RealEstateDBManager
from datetime import datetime

load_dotenv()

class SeoulMarketCollector:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=self.api_key)
        self.model = "gemini-3.1-pro-preview"
        self.db = RealEstateDBManager()

    def fetch_current_prices(self):
        """
        로컬 DB에 저장된 실제 실거래 통계 데이터를 가져와 분석합니다.
        """
        print(f"[Market Collector] 로컬 DB에서 최신 실거래 통계 추출 중...")
        
        # 1. 최신 7일간의 트렌드 데이터 가져오기
        trends = self.db.get_latest_trends(days=7)
        
        if not trends:
            print("DB에 통계 데이터가 부족합니다. 기본 정보를 반환합니다.")
            return None

        # 2. 데이터를 텍스트로 요약하여 LLM에게 분석 요청 (통찰 도출용)
        # 매매, 전세, 월세 데이터를 모두 포함
        summary_text = "\n".join([
            f"- {t['log_date']} {t['district_name']}: "
            f"매매 {int(t['avg_price']):,}만원(건수 {t['trade_count']}, 전일대비 {t['prev_diff_rate']:.2f}%), "
            f"전세 {int(t['avg_jeonse']):,}만원(건수 {t['jeonse_count']}), "
            f"월세 {int(t['avg_wolse']):,}만원(건수 {t['wolse_count']})"
            for t in trends[:50] 
        ])
        
        prompt = f"""
        당신은 부동산 데이터 분석가입니다. 아래 제공된 최근 7일간의 서울시 구별 실거래 통계 데이터(매매/전세/월세)를 분석하여 요약 보고서를 JSON으로 작성하세요.
        
        [실거래 통계 데이터]
        {summary_text}
        
        [응답 형식]
        {{
            "date": "{datetime.now().strftime('%Y-%m-%d')}",
            "districts": [
                {{
                    "name": "구이름",
                    "sale_trend": "상승/하락/보합",
                    "sale_price": "최근 평균가 정보",
                    "jeonse_price": "최근 전세 평균가 정보",
                    "wolse_price": "최근 월세 평균가 정보",
                    "status": "매매 및 임대차 시장 특징 1줄 요약"
                }}
            ],
            "hot_spot": "변동률이 크거나 거래가 활발한 지역",
            "summary": "현재 서울 매매 및 임대차 시장의 지배적인 분위기 요약"
        }}
        """
        
        response = self.client.models.generate_content(model=self.model, contents=prompt).text
        try:
            import re
            json_str = re.search(r'\{.*\}', response, re.DOTALL).group()
            return json.loads(json_str)
        except Exception as e:
            print(f"Market Collector 분석 오류: {e}")
            return None

class MarketWriter:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = "gemini-3.1-pro-preview"

    def generate_briefing(self, market_data):
        print(f"[Market Writer] 서울 시세 브리핑 포스트 생성 중...")
        
        prompt = f"""
        당신은 부동산 시세 분석 전문가입니다. 아래 수집된 서울시 구별 시세 데이터(매매 및 전월세)를 바탕으로 
        시민들이 매일 읽기 좋은 '일일 시세 브리핑' 블로그 포스트를 마크다운으로 작성하세요.
        
        [중요 지시사항]
        - **응답에는 오직 마크다운 본문만 포함하세요.**
        - 인사말 등 서론 없이 바로 리포트 제목(#)부터 시작하세요.
        
        [수집 데이터]:
        {json.dumps(market_data, ensure_ascii=False, indent=2)}
        
        [작성 가이드]
        1. **시각적 강조**: 상승(▲), 하락(▼), 보합(—) 이모지를 적절히 사용하여 시세 변동을 한눈에 보여주세요.
        2. **표(Table) 활용**: 구별 시세 정보(매매, 전세, 월세)를 깔끔한 마크다운 표로 정리하세요.
        3. **분석 내용**: 단순히 수치만 나열하지 말고, 매매가 대비 전세가 추이나 특정 지역의 임대차 시장 특이점을 한두 문장 덧붙여주세요.
        4. **디자인 요소**: EstateIntel의 신뢰감 있는 스타일을 위해 구조화된 섹션과 굵은 글씨를 활용하세요.
        [데이터 카드]: 상단에 아래 HTML 구조를 사용하여 오늘의 요약을 보여주세요.
           <div class="data-card-grid-rows">
             <div class="data-card"><div class="label">🎯 오늘의 핫스팟</div><div class="value">{market_data.get('hot_spot')}</div></div>
             <div class="data-card"><div class="label">📊 서울 전체 동향</div><div class="value">{market_data.get('summary')}</div></div>
           </div>

        """
        
        # 모든 출처 정리 (시세 정보는 종합 데이터이므로 출처를 명시)
        sources_footer = "\n\n---\n**참고 자료 및 출처**\n\n- [국토교통부 실거래가 공개시스템](https://rt.molit.go.kr/)\n- [한국부동산원 부동산통계정보시스템](https://www.reb.or.kr/)"
        
        return self.client.models.generate_content(model=self.model, contents=prompt).text + sources_footer
