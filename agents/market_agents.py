import os
import json
from datetime import datetime
from db_manager import RealEstateDBManager
from opencode_helper import OpenCodeHelper

class SeoulMarketCollector:
    def __init__(self):
        self.db = RealEstateDBManager()

    def fetch_current_prices(self):
        """OpenCode Market Collector 에이전트를 사용하여 통계 분석"""
        print(f"[Market Collector] 로컬 DB 데이터를 분석 중...")
        
        trends = self.db.get_latest_trends(days=7)
        if not trends: return None

        summary_text = "\n".join([
            f"- {t['log_date']} {t['district_name']}: 평균 {int(t['avg_price']):,}만원 (전일대비 {t['prev_diff_rate']:.2f}%)"
            for t in trends[:50]
        ])
        
        inputs = {
            "current_date": datetime.now().strftime('%Y-%m-%d'),
            "summary_text": summary_text
        }
        
        response = OpenCodeHelper.run("market_collector", inputs)
        return OpenCodeHelper.parse_json(response)

class MarketWriter:
    def generate_briefing(self, market_data):
        """OpenCode Market Writer 에이전트를 사용하여 브리핑 작성"""
        print(f"[Market Writer] 서울 시세 브리핑 포스트 생성 중...")
        
        inputs = {
            "hot_spot": market_data.get('hot_spot'),
            "summary": market_data.get('summary'),
            "date": market_data.get('date'),
            "market_data_json": json.dumps(market_data, ensure_ascii=False, indent=2)
        }
        
        main_content = OpenCodeHelper.run("market_writer", inputs)
        
        sources_footer = "\n\n---\n**참고 자료 및 출처**\n\n- [국토교통부 실거래가 공개시스템](https://rt.molit.go.kr/)\n- [한국부동산원 부동산통계정보시스템](https://www.reb.or.kr/)"
        
        return (main_content if main_content else "브리핑 생성 실패") + sources_footer
