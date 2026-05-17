import os
import feedparser
from google import genai
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

class RealEstateResearcher:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=self.api_key)
        self.model_lite = "gemini-3.1-flash-lite"
        self.history_file = os.path.join(os.path.dirname(__file__), "history.txt")
        self.queries = [
            "주간+아파트+가격+동향", 
            "지역별+아파트+시세+등락",
            "재건축+재개발+현황",
            "부동산+정책+발표",
            "네이버부동산+주요+뉴스",
            "매일경제+부동산+분석",
            "한국경제+집코노미+트렌드",
            "KB부동산+시장+리포트",
            "땅집고+부동산+분석"
        ]

    def _get_history(self):
        if os.path.exists(self.history_file):
            with open(self.history_file, "r") as f: return f.read().splitlines()
        return []

    def fetch_multi_source_topics(self):
        history = self._get_history()
        raw_news = []
        today = datetime.now().strftime("%d %b %Y") # RSS 날짜 형식 대응
        
        print(f"최신 뉴스 대량 수집 및 필터링 중...")
        for query in self.queries:
            url = f"https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"
            feed = feedparser.parse(url)
            for e in feed.entries[:10]: # 더 많이 수집
                if e.link not in history:
                    raw_news.append({
                        "title": e.title,
                        "summary": e.summary,
                        "link": e.link,
                        "source": e.source.get('title', '뉴스') if hasattr(e, 'source') else '뉴스',
                        "published": e.published
                    })
        return raw_news

    def group_and_select_best_theme(self, topics):
        """뉴스들을 분석하여 연관된 뉴스들을 하나의 '테마'로 묶음"""
        if not topics: return None
        
        titles = "\n".join([f"- {t['title']}" for t in topics])
        prompt = f"""
        다음 부동산 뉴스 목록을 분석하여, 오늘 가장 중요하게 다뤄야 할 '하나의 핵심 주제'를 정하고, 
        그 주제와 직접적으로 연관된 뉴스들을 최대 3-4개 골라 JSON으로 응답하세요.
        반드시 다음 형식을 지키세요:
        {{ "theme_title": "핵심 주제 제목", "related_indices": [0, 2, 5] }}
        
        뉴스 목록:
        {titles}
        """
        
        response = self.client.models.generate_content(model=self.model_lite, contents=prompt).text
        try:
            import json, re
            json_str = re.search(r'\{.*\}', response, re.DOTALL).group()
            data = json.loads(json_str)
            
            selected_news = [topics[i] for i in data['related_indices'] if i < len(topics)]
            return {
                "title": data['theme_title'],
                "news_items": selected_news
            }
        except:
            return {"title": topics[0]['title'], "news_items": [topics[0]]}

    def save_to_history(self, news_items):
        with open(self.history_file, "a") as f:
            for item in news_items:
                f.write(item['link'] + "\n")
        print(f"히스토리에 {len(news_items)}건의 출처 저장 완료.")
