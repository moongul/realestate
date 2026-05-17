import os
import time
from db_manager import RealEstateDBManager
from datetime import datetime, timedelta

def initialize():
    db = RealEstateDBManager()
    
    # 서울시 25개 구 코드
    seoul_districts = [
        "11110", "11140", "11170", "11200", "11215", "11230", "11260", "11290",
        "11305", "11320", "11350", "11380", "11410", "11440", "11470", "11500",
        "11530", "11545", "11560", "11590", "11620", "11650", "11680", "11710", "11740"
    ]
    
    # 최근 3개월 데이터 수집 (초기 적재는 시간이 걸리므로 3개월로 시작)
    # 1년치는 데이터량이 많아 API 할당량을 초과할 수 있습니다.
    current_date = datetime.now()
    months_to_fetch = []
    for i in range(3):
        target_month = (current_date - timedelta(days=i*30)).strftime("%Y%m")
        months_to_fetch.append(target_month)
    
    print(f"--- 서울시 실거래 데이터 초기 적재 시작 (대상 월: {months_to_fetch}) ---")
    
    for ym in months_to_fetch:
        print(f"\n[월: {ym}] 수집 중...")
        for code in seoul_districts:
            # 매매 데이터 수집
            db.fetch_and_save_trades(code, ym)
            # 전월세 데이터 수집
            db.fetch_and_save_rents(code, ym)
            time.sleep(0.1) # API 부하 방지
            
    print("\n--- 통계 데이터 계산 중... ---")
    # 수집된 데이터를 바탕으로 일별 통계 계산 (최근 30일치)
    for i in range(30, -1, -1):
        target_date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        db.calculate_daily_stats(target_date)
        
    print("\n--- 초기화 완료! ---")

if __name__ == "__main__":
    initialize()
