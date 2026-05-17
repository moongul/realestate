import os
import sqlite3
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

class RealEstateDBManager:
    def __init__(self, db_path="agents/real_estate.db"):
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "real_estate.db")
        self.api_key = os.getenv("MOLIT_API_KEY") # 공공데이터포털 디코딩 키
        self._init_db()

    def _init_db(self):
        """데이터베이스 및 테이블 초기화"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        # 1. 원천 매매 데이터 테이블
        cur.execute("""
            CREATE TABLE IF NOT EXISTS raw_trades (
                trade_id TEXT PRIMARY KEY,
                district_code TEXT,
                apt_name TEXT,
                exclusive_area REAL,
                trade_amount INTEGER,
                trade_date TEXT,
                cancel_yn TEXT DEFAULT 'N',
                cancel_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 2. 원천 전월세 데이터 테이블
        cur.execute("""
            CREATE TABLE IF NOT EXISTS raw_rents (
                rent_id TEXT PRIMARY KEY,
                district_code TEXT,
                apt_name TEXT,
                exclusive_area REAL,
                deposit INTEGER,
                monthly_rent INTEGER,
                trade_date TEXT,
                rent_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 3. 구 단위 일일 통계 테이블
        cur.execute("""
            CREATE TABLE IF NOT EXISTS district_trend (
                log_date TEXT,
                district_code TEXT,
                district_name TEXT,
                avg_price REAL,
                trade_count INTEGER,
                prev_diff_rate REAL,
                avg_jeonse REAL,
                jeonse_count INTEGER,
                avg_wolse REAL,
                wolse_count INTEGER,
                PRIMARY KEY (log_date, district_code)
            )
        """)
        
        conn.commit()
        conn.close()

    def fetch_and_save_trades(self, district_code, ym):
        """특정 구, 특정 월의 매매 실거래 데이터를 가져와 저장"""
        service_name = "RTMSDataSvcAptTrade"
        endpoint = "getRTMSDataSvcAptTrade" 
        url = f"http://apis.data.go.kr/1613000/{service_name}/{endpoint}"
        
        # numOfRows=10000 추가하여 누락 없이 수집
        query_url = f"{url}?serviceKey={self.api_key}&LAWD_CD={district_code}&DEAL_YMD={ym}&numOfRows=10000"
        
        try:
            response = requests.get(query_url, timeout=15)
            if response.status_code != 200:
                print(f"API 호출 실패 (HTTP {response.status_code})")
                return False
            
            content = response.content.decode('utf-8')
            if "<resultMsg>" in content and "OK" not in content:
                print(f"API 에러 응답: {content}")
                return False
                
            root = ET.fromstring(response.content)
            items = root.findall('.//item')
            
            if not items:
                print(f"[매매 {ym}] {district_code}: 검색된 데이터 없음")
                return True

            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            
            count = 0
            for item in items:
                apt_name = item.findtext('aptNm', '').strip()
                amount_str = item.findtext('dealAmount', '0').replace(',', '')
                amount = int(amount_str) if amount_str else 0
                area_str = item.findtext('excluUseAr', '0')
                area = float(area_str) if area_str else 0.0
                
                y = item.findtext('dealYear')
                m = item.findtext('dealMonth')
                d = item.findtext('dealDay')
                
                if not all([y, m, d]):
                    continue
                    
                trade_date = f"{y}-{m.zfill(2)}-{d.zfill(2)}"
                cancel_type = item.findtext('cdealType', '').strip()
                cancel_yn = 'Y' if cancel_type == 'O' else 'N'
                cancel_date = item.findtext('cdealDay', '').strip()
                
                trade_id = f"{trade_date}_{apt_name}_{amount}_{area}"
                
                cur.execute("""
                    INSERT INTO raw_trades (trade_id, district_code, apt_name, exclusive_area, trade_amount, trade_date, cancel_yn, cancel_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(trade_id) DO UPDATE SET
                        cancel_yn = excluded.cancel_yn,
                        cancel_date = excluded.cancel_date
                """, (trade_id, district_code, apt_name, area, amount, trade_date, cancel_yn, cancel_date))
                count += 1
            
            conn.commit()
            conn.close()
            print(f"[매매 {ym}] 구 코드 {district_code}: {count}건 저장 완료")
            return True
            
        except Exception as e:
            print(f"매매 데이터 수집 중 오류 발생: {e}")
            return False

    def fetch_and_save_rents(self, district_code, ym):
        """특정 구, 특정 월의 전월세 실거래 데이터를 가져와 저장"""
        service_name = "RTMSDataSvcAptRent"
        endpoint = "getRTMSDataSvcAptRent" 
        url = f"http://apis.data.go.kr/1613000/{service_name}/{endpoint}"
        
        # numOfRows=10000 추가하여 누락 없이 수집
        query_url = f"{url}?serviceKey={self.api_key}&LAWD_CD={district_code}&DEAL_YMD={ym}&numOfRows=10000"
        
        try:
            response = requests.get(query_url, timeout=15)
            if response.status_code != 200:
                print(f"API 호출 실패 (HTTP {response.status_code})")
                return False
            
            content = response.content.decode('utf-8')
            if "<resultMsg>" in content and "OK" not in content:
                print(f"API 에러 응답: {content}")
                return False
                
            root = ET.fromstring(response.content)
            items = root.findall('.//item')
            
            if not items:
                print(f"[전월세 {ym}] {district_code}: 검색된 데이터 없음")
                return True

            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            
            count = 0
            for item in items:
                apt_name = item.findtext('aptNm', '').strip()
                deposit_str = item.findtext('deposit', '0').replace(',', '')
                deposit = int(deposit_str) if deposit_str else 0
                rent_str = item.findtext('monthlyRent', '0').replace(',', '')
                monthly_rent = int(rent_str) if rent_str else 0
                area_str = item.findtext('excluUseAr', '0')
                area = float(area_str) if area_str else 0.0
                
                y = item.findtext('dealYear')
                m = item.findtext('dealMonth')
                d = item.findtext('dealDay')
                
                if not all([y, m, d]):
                    continue
                    
                trade_date = f"{y}-{m.zfill(2)}-{d.zfill(2)}"
                
                # 전월세 구분 (월세가 0이면 전세)
                rent_type = '월세' if monthly_rent > 0 else '전세'
                
                # 중복 방지를 위한 고유 ID 생성 (거래일+단지명+보증금+월세+면적)
                rent_id = f"{trade_date}_{apt_name}_{deposit}_{monthly_rent}_{area}"
                
                cur.execute("""
                    INSERT INTO raw_rents (rent_id, district_code, apt_name, exclusive_area, deposit, monthly_rent, trade_date, rent_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(rent_id) DO NOTHING
                """, (rent_id, district_code, apt_name, area, deposit, monthly_rent, trade_date, rent_type))
                count += 1
            
            conn.commit()
            conn.close()
            print(f"[전월세 {ym}] 구 코드 {district_code}: {count}건 저장 완료")
            return True
            
        except Exception as e:
            print(f"전월세 데이터 수집 중 오류 발생: {e}")
            return False

    def calculate_daily_stats(self, target_date=None):
        """특정 날짜의 구별 통계를 계산하여 trend 테이블에 저장 (7일 이동평균 적용)"""
        if target_date is None:
            target_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        seoul_districts = {
            "11110": "종로구", "11140": "중구", "11170": "용산구", "11200": "성동구",
            "11215": "광진구", "11230": "동대문구", "11260": "중랑구", "11290": "성북구",
            "11305": "강북구", "11320": "도봉구", "11350": "노원구", "11380": "은평구",
            "11410": "서대문구", "11440": "마포구", "11470": "양천구", "11500": "강서구",
            "11530": "구로구", "11545": "금천구", "11560": "영등포구", "11590": "동작구",
            "11620": "관악구", "11650": "서초구", "11680": "강남구", "11710": "송파구",
            "11740": "강동구"
        }
        
        end_dt = datetime.strptime(target_date, "%Y-%m-%d")
        start_date = (end_dt - timedelta(days=6)).strftime("%Y-%m-%d")

        for code, name in seoul_districts.items():
            # 1. 매매 통계
            cur.execute("""
                SELECT AVG(trade_amount), COUNT(*) FROM raw_trades
                WHERE district_code = ? AND trade_date BETWEEN ? AND ? 
                AND cancel_yn != 'Y' AND trade_amount < 500000 
            """, (code, start_date, target_date))
            avg_price, trade_count = cur.fetchone()
            avg_price = avg_price if avg_price else 0
            trade_count = trade_count if trade_count else 0
            
            # 2. 전세 통계
            cur.execute("""
                SELECT AVG(deposit), COUNT(*) FROM raw_rents
                WHERE district_code = ? AND trade_date BETWEEN ? AND ? 
                AND rent_type = '전세'
            """, (code, start_date, target_date))
            avg_jeonse, jeonse_count = cur.fetchone()
            avg_jeonse = avg_jeonse if avg_jeonse else 0
            jeonse_count = jeonse_count if jeonse_count else 0

            # 3. 월세 통계 (보증금 제외하고 순수 월세 평균)
            cur.execute("""
                SELECT AVG(monthly_rent), COUNT(*) FROM raw_rents
                WHERE district_code = ? AND trade_date BETWEEN ? AND ? 
                AND rent_type = '월세'
            """, (code, start_date, target_date))
            avg_wolse, wolse_count = cur.fetchone()
            avg_wolse = avg_wolse if avg_wolse else 0
            wolse_count = wolse_count if wolse_count else 0
            
            # 4. 변동률 및 저장
            if trade_count > 0 or jeonse_count > 0 or wolse_count > 0:
                prev_date = (end_dt - timedelta(days=1)).strftime("%Y-%m-%d")
                cur.execute("SELECT avg_price FROM district_trend WHERE log_date = ? AND district_code = ?", (prev_date, code))
                prev_row = cur.fetchone()
                prev_avg = prev_row[0] if prev_row else avg_price
                diff_rate = ((avg_price - prev_avg) / prev_avg * 100) if prev_avg > 0 else 0
                
                cur.execute("""
                    INSERT INTO district_trend (log_date, district_code, district_name, avg_price, trade_count, prev_diff_rate, avg_jeonse, jeonse_count, avg_wolse, wolse_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(log_date, district_code) DO UPDATE SET
                        avg_price = excluded.avg_price,
                        trade_count = excluded.trade_count,
                        prev_diff_rate = excluded.prev_diff_rate,
                        avg_jeonse = excluded.avg_jeonse,
                        jeonse_count = excluded.jeonse_count,
                        avg_wolse = excluded.avg_wolse,
                        wolse_count = excluded.wolse_count
                """, (target_date, code, name, avg_price, trade_count, diff_rate, avg_jeonse, jeonse_count, avg_wolse, wolse_count))
                
        conn.commit()
        conn.close()
        print(f"{target_date} 통계 계산 완료 (매매/전월세 포함)")

    def export_latest_stats(self, target_path=None):
        """Astro 프론트엔드에서 사용할 최신 요약 데이터를 JSON으로 내보냄"""
        if target_path is None:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            target_path = os.path.join(project_root, "blog/src/data/latest_stats.json")
            
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # 1. 최신 날짜 찾기
        cur.execute("SELECT MAX(log_date) FROM district_trend")
        latest_date = cur.fetchone()[0]
        
        if not latest_date:
            return False
            
        # 2. 최신 날짜의 모든 구 데이터 가져오기
        cur.execute("SELECT * FROM district_trend WHERE log_date = ? ORDER BY prev_diff_rate DESC", (latest_date,))
        rows = cur.fetchall()
        districts = [dict(row) for row in rows]
        
        # 3. 주요 지표 계산
        total_trades = sum(d['trade_count'] for d in districts)
        avg_seoul_price = sum(d['avg_price'] for d in districts) / len(districts) if districts else 0
        
        # 상위/하위 3개구
        top_gainers = districts[:3]
        top_losers = districts[-3:]
        
        data = {
            "last_updated": latest_date,
            "total_trades": total_trades,
            "avg_seoul_price": int(avg_seoul_price),
            "top_gainers": top_gainers,
            "top_losers": top_losers,
            "all_districts": districts
        }
        
        import json
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        print(f"최신 통계 JSON 내보내기 완료: {target_path}")
        conn.close()
        return True
