import os
import json
import re
from google import genai
from dotenv import load_dotenv

load_dotenv()

class DataAnalyst:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = "gemini-3.1-pro-preview" # 높은 데이터 정확도를 위해 Pro 사용

    def analyze(self, theme_info):
        print(f"[Data Analyst] {len(theme_info['news_items'])}개의 뉴스에서 핵심 수치 및 트렌드 추출 중...")
        
        sources_text = "\n\n".join([
            f"제목: {n['title']}\n요약: {n['summary']}\n출처: {n['source']}" 
            for n in theme_info['news_items']
        ])
        
        prompt = f"""
        당신은 꼼꼼한 데이터 분석가입니다. 주어진 뉴스 데이터를 바탕으로 명확한 수치와 팩트만을 추출하세요.
        외부 지식을 섞지 말고, 주어진 텍스트 내에서만 분석하세요.
        
        [주제 테마]: {theme_info['title']}
        
        [뉴스 데이터]:
        {sources_text}
        
        다음 항목들을 분석하여 JSON 형태로 응답하세요. 마크다운 코드 블록(```json)을 사용하지 말고 순수 JSON 문자열만 출력하세요.
        {{
            "market_vibe": "시장 분위기 요약 (예: 강보합, 하락세)",
            "key_factors": "주요 호재나 악재 (예: GTX-C, 대출 규제)",
            "attention_level": "관심/주의 단계 (예: 적극 매수, 관망, 주의)",
            "regional_data": [
                {{"region": "지역명", "trend": "동향 요약", "price_info": "언급된 수치나 가격 정보", "note": "비고"}}
            ],
            "expert_insight": "뉴스에서 도출할 수 있는 실거주자/투자자를 위한 시사점 1~2문장"
        }}
        """
        
        response = self.client.models.generate_content(model=self.model, contents=prompt).text
        try:
            # 안전한 파싱
            json_str = re.search(r'\{.*\}', response, re.DOTALL).group()
            return json.loads(json_str)
        except Exception as e:
            print(f"Data Analyst JSON 파싱 오류: {e}")
            return {
                "market_vibe": "정보 부족", "key_factors": "정보 부족", "attention_level": "관망",
                "regional_data": [], "expert_insight": "현재 수집된 데이터로는 명확한 시사점을 도출하기 어렵습니다."
            }

class PersonaEditor:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = "gemini-3.1-flash-lite-preview" # 문장 교정과 톤앤매너에 최적화

    def edit(self, draft_text):
        print(f"[Persona Editor] 브랜드 톤앤매너 적용 및 교정 중...")
        
        prompt = f"""
        당신은 수석 에디터입니다. 아래 부동산 분석 리포트 초안을 교정/교열하여 더 읽기 쉽고 매력적으로 만드세요.
        
        [중요 지시사항]
        - **응답의 시작과 끝에는 오직 수정된 본문 내용만 포함하세요.**
        - "수정해 드립니다", "교정본입니다"와 같은 인사말이나 설명(preamble)을 **절대 하지 마세요.**
        - 수정된 결과는 바로 마크다운으로 시작해야 합니다.
        
        [톤앤매너 가이드]
        1. **친절하고 세련된 전문가 느낌**: 잡지 칼럼처럼 자연스럽고 신뢰감 있는 문체로 수정하세요.
        2. **Airbnb 스타일**: 여유롭고 따뜻한 톤을 유지하세요.
        3. **포맷 유지**: 기존 초안에 적용된 마크다운 구조(데이터 카드 HTML, Blockquote, 테이블, ### 📍 등)는 **절대 훼손하지 마세요**.
        4. **따옴표**: 가급적이면 스마트 따옴표(‘, ’) 대신 표준 따옴표(', ")를 사용하세요.

        [초안]:
        {draft_text}
        """
        return self.client.models.generate_content(model=self.model, contents=prompt).text

class SEOOptimizer:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = "gemini-3.1-flash-lite-preview" # 빠르고 가벼운 메타데이터 생성

    def optimize(self, final_text, theme_title):
        print(f"[SEO Optimizer] 검색 엔진 최적화 메타데이터 및 이미지 키워드 추출 중...")
        
        prompt = f"""
        아래 부동산 블로그 포스트 본문을 읽고 SEO 최적화 메타데이터를 JSON 형태로 작성하세요.
        마크다운 코드 블록 없이 순수 JSON만 출력하세요.
        
        [가이드]
        1. title: 클릭을 유도하는 매력적인 제목 (최대 50자). 테마 "{theme_title}"를 반영.
        2. description: 검색 결과에 노출될 요약문 (100자 내외).
        
        [본문 미리보기]:
        {final_text[:800]}
        
        JSON 포맷:
        {{
            "title": "...",
            "description": "..."
        }}
        """
        response = self.client.models.generate_content(model=self.model, contents=prompt).text
        try:
            json_str = re.search(r'\{.*\}', response, re.DOTALL).group()
            return json.loads(json_str)
        except Exception as e:
            print(f"SEO Optimizer JSON 파싱 오류: {e}")
            return {
                "title": theme_title, 
                "description": theme_title, 
                "image_keyword": "realestate"
            }
