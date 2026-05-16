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
        
        # 1. 원천 거래 데이터 테이블
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
        
        # 2. 구 단위 일일 통계 테이블
        cur.execute("""
            CREATE TABLE IF NOT EXISTS district_trend (
                log_date TEXT,
                district_code TEXT,
                district_name TEXT,
                avg_price REAL,
                trade_count INTEGER,
                prev_diff_rate REAL,
                PRIMARY KEY (log_date, district_code)
            )
        """)
        
        conn.commit()
        conn.close()

    def fetch_and_save_trades(self, district_code, ym):
        """특정 구, 특정 월의 실거래 데이터를 가져와 저장"""
        # 사용자가 요청한 표준 아파트 매매 실거래가 API 주소
        service_name = "RTMSDataSvcAptTrade"
        endpoint = "getRTMSDataSvcAptTrade" 
        url = f"http://apis.data.go.kr/1613000/{service_name}/{endpoint}"
        
        # 인코딩된 키 직접 사용 (double-encoding 방지)
        query_url = f"{url}?serviceKey={self.api_key}&LAWD_CD={district_code}&DEAL_YMD={ym}"
        
        try:
            response = requests.get(query_url, timeout=15)
            if response.status_code != 200:
                print(f"API 호출 실패 (HTTP {response.status_code})")
                return False
            
            # 응답 내용 확인 (에러 메시지 체크용)
            content = response.content.decode('utf-8')
            if "<resultMsg>" in content and "OK" not in content:
                print(f"API 에러 응답: {content}")
                return False
                
            root = ET.fromstring(response.content)
            items = root.findall('.//item')
            
            if not items:
                # 데이터가 없는 경우 (정상일 수 있음)
                print(f"[{ym}] {district_code}: 검색된 데이터 없음")
                return True

            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            
            count = 0
            for item in items:
                # 데이터 파싱 (영어 필드명 대응)
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
                
                # 취소 여부 (cdealType: 'O'가 취소)
                cancel_type = item.findtext('cdealType', '').strip()
                cancel_yn = 'Y' if cancel_type == 'O' else 'N'
                cancel_date = item.findtext('cdealDay', '').strip()
                
                # 중복 방지를 위한 고유 ID 생성 (거래일+단지명+금액+면적)
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
            print(f"[{ym}] 구 코드 {district_code}: {count}건 저장 완료")
            return True
            
        except Exception as e:
            print(f"데이터 수집 중 오류 발생: {e}")
            return False

    def calculate_daily_stats(self, target_date=None):
        """특정 날짜의 구별 통계를 계산하여 trend 테이블에 저장"""
        if target_date is None:
            target_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        # 서울시 구 코드 매핑 (일부)
        seoul_districts = {
            "11110": "종로구", "11140": "중구", "11170": "용산구", "11200": "성동구",
            "11215": "광진구", "11230": "동대문구", "11260": "중랑구", "11290": "성북구",
            "11305": "강북구", "11320": "도봉구", "11350": "노원구", "11380": "은평구",
            "11410": "서대문구", "11440": "마포구", "11470": "양천구", "11500": "강서구",
            "11530": "구로구", "11545": "금천구", "11560": "영등포구", "11590": "동작구",
            "11620": "관악구", "11650": "서초구", "11680": "강남구", "11710": "송파구",
            "11740": "강동구"
        }
        
        for code, name in seoul_districts.items():
            # 평균가 및 거래건수 계산 (취소 거래 제외)
            cur.execute("""
                SELECT AVG(trade_amount), COUNT(*) FROM raw_trades
                WHERE district_code = ? AND trade_date = ? AND cancel_yn != 'O'
            """, (code, target_date))
            
            avg_price, count = cur.fetchone()
            
            if count > 0:
                # 전일 평균가 가져오기 (변동률 계산용)
                prev_date = (datetime.strptime(target_date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
                cur.execute("SELECT avg_price FROM district_trend WHERE log_date = ? AND district_code = ?", (prev_date, code))
                prev_row = cur.fetchone()
                prev_avg = prev_row[0] if prev_row else avg_price
                
                diff_rate = ((avg_price - prev_avg) / prev_avg * 100) if prev_avg > 0 else 0
                
                cur.execute("""
                    INSERT INTO district_trend (log_date, district_code, district_name, avg_price, trade_count, prev_diff_rate)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(log_date, district_code) DO UPDATE SET
                        avg_price = excluded.avg_price,
                        trade_count = excluded.trade_count,
                        prev_diff_rate = excluded.prev_diff_rate
                """, (target_date, code, name, avg_price, count, diff_rate))
                
        conn.commit()
        conn.close()
        print(f"{target_date} 통계 계산 완료")

    def get_latest_trends(self, days=7):
        """최근 7일간의 주요 통계 데이터 반환 (에이전트용)"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        cur.execute("""
            SELECT * FROM district_trend 
            ORDER BY log_date DESC, prev_diff_rate DESC 
            LIMIT ?
        """, (days * 25,)) # 25개구 * 일수
        
        rows = cur.fetchall()
        conn.close()
        return [dict(row) for row in rows]
