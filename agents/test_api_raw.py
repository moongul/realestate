import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_api():
    api_key = os.getenv("MOLIT_API_KEY")
    district_code = "11680" # 강남구
    ym = "202401" # 2024년 1월로 테스트 (데이터가 확실히 있는 과거)
    
    url = "http://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade"
    query_url = f"{url}?serviceKey={api_key}&LAWD_CD={district_code}&DEAL_YMD={ym}"
    
    print(f"Testing URL: {query_url}")
    response = requests.get(query_url)
    print(f"Status Code: {response.status_code}")
    print("Response Content:")
    print(response.text[:2000])

if __name__ == "__main__":
    test_api()
