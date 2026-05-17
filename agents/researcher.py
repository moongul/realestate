import os
import feedparser
from google import genai
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

class RealEstateResearcher:
    def __init__(self):
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

    def _get_existing_titles(self):
        """기존 블로그 포스트들의 제목을 가져와 중복 주제 방지"""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        blog_dir = os.path.join(project_root, "blog/src/content/blog")
        titles = []
        if os.path.exists(blog_dir):
            for f in os.listdir(blog_dir):
                if f.endswith(".md"):
                    # 파일명에서 날짜를 제외한 제목 키워드 추출
                    titles.append(f)
        return titles[-5:] # 최근 5개 정도만 참고

    def group_and_select_best_theme(self, topics):
        """OpenCode Researcher 에이전트를 사용하여 테마 선정"""
        if not topics: return None
        
        from opencode_helper import OpenCodeHelper
        
        recent_titles = self._get_existing_titles()
        
        inputs = {
            "history_text": "\n".join([f"- {t}" for t in recent_titles]),
            "titles_text": "\n".join([f"- {t['title']}" for t in topics])
        }
        
        response = OpenCodeHelper.run("researcher", inputs)
        data = OpenCodeHelper.parse_json(response)
        
        if data and 'related_indices' in data:
            try:
                selected_news = [topics[i] for i in data['related_indices'] if i < len(topics)]
                return {
                    "title": data['theme_title'],
                    "news_items": selected_news
                }
            except Exception as e:
                print(f"Researcher 결과 처리 오류: {e}")
        
        # 폴백: 첫 번째 뉴스 사용
        return {"title": topics[0]['title'], "news_items": [topics[0]]}

    def save_to_history(self, news_items):
        with open(self.history_file, "a") as f:
            for item in news_items:
                f.write(item['link'] + "\n")
        print(f"히스토리에 {len(news_items)}건의 출처 저장 완료.")
