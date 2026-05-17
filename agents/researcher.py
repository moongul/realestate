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
        """뉴스들을 분석하여 최근 주제와 겹치지 않는 새로운 '테마'를 선정"""
        if not topics: return None
        
        recent_titles = self._get_existing_titles()
        titles_text = "\n".join([f"- {t['title']}" for t in topics])
        history_text = "\n".join([f"- {t}" for t in recent_titles])
        
        prompt = f"""
        당신은 트렌드에 민감한 부동산 연구원입니다. 
        아래 '신규 뉴스 목록'을 분석하여 오늘 블로그에 발행할 '하나의 핵심 주제'를 선정하세요.
        
        [최근 발행된 주제들 (가급적 피할 것)]:
        {history_text}
        
        [신규 뉴스 목록]:
        {titles_text}
        
        [선정 가이드라인]
        1. **신선함**: 최근 발행된 주제들과 핵심 키워드가 겹치지 않는 '새로운 각도'의 뉴스를 우선적으로 고려하세요.
        2. **영향력**: 신선하면서도 시장에 미치는 영향이 큰 주제를 선정하세요.
        3. **구조화**: 선정된 주제와 직접적으로 연관된 뉴스들(최대 4개)을 골라 JSON으로 응답하세요.
        
        응답 형식 (JSON):
        {{ "theme_title": "신선하고 매력적인 주제 제목", "related_indices": [인덱스 번호들] }}
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
