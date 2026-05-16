import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

class BlogWriter:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=self.api_key)
        self.model_complex = "gemini-3.1-pro-preview"

    def generate_post(self, theme_info, analyzed_data):
        """Data Analyst가 추출한 구조화된 데이터를 바탕으로 리포트 초안 작성"""
        
        print(f"[Writer] 구조화된 데이터를 바탕으로 리포트 초안 집필 중...")
        
        # 분석된 데이터를 텍스트로 변환하여 프롬프트에 주입 (토큰 절약 및 정확도 향상)
        regional_text = ""
        for r in analyzed_data.get('regional_data', []):
            regional_text += f"- 지역: {r.get('region')}\n  동향: {r.get('trend')}\n  가격정보: {r.get('price_info')}\n  비고: {r.get('note')}\n\n"

        prompt = f"""
        당신은 주거 부동산 전문 분석가입니다. 아래 분석된 핵심 데이터를 바탕으로 가독성이 뛰어나고 시각적으로 구조화된 리포트를 작성하세요.
        
        [주제 테마]: {theme_info['title']}
        
        [분석 데이터]
        - 시장 분위기: {analyzed_data.get('market_vibe')}
        - 핵심 키워드: {analyzed_data.get('key_factors')}
        - 주의 단계: {analyzed_data.get('attention_level')}
        - 전문가 시사점: {analyzed_data.get('expert_insight')}
        
        [지역별 세부 데이터]
        {regional_text}
        
        [작성 스타일 가이드]
        1. **시각적 요약 카드**: 본문 시작 직후(서론 전)에 아래 HTML 구조를 사용하여 핵심 지표 3개를 요약하세요. 데이터의 내용을 채워넣으세요.
           <div class="data-card-grid">
             <div class="data-card"><div class="label">시장 분위기</div><div class="value">{analyzed_data.get('market_vibe', '보합')}</div></div>
             <div class="data-card"><div class="label">핵심 키워드</div><div class="value">{analyzed_data.get('key_factors', '이슈 없음')}</div></div>
             <div class="data-card"><div class="label">주의 단계</div><div class="value">{analyzed_data.get('attention_level', '관망')}</div></div>
           </div>

        2. **핵심 요약 (Blockquote)**: 1번 섹션 시작 전에 마크다운 인용문(`> `)을 사용하여 전체 리포트의 핵심 결론을 요약하세요. 첫 줄은 **핵심 요약**으로 시작하세요.

        3. **구조화된 표**: 지역별 세부 데이터를 마크다운 표(Table)로 요약하여 배치하세요. 컬럼은 [지역명, 동향, 가격정보, 비고]를 사용하세요.

        4. **지역별 상세 분석**: 표 아래에 지역별 특징을 설명할 때는 `### 📍 [지역명]` 형식을 사용하세요.

        5. **전문가 제언 (Blockquote)**: 마지막 섹션 시작 부분에 마크다운 인용문(`> `)을 사용하여 '전문가 시사점'을 확장하여 강조하세요. 첫 줄은 **전문가 제언: [핵심주제]**로 시작하세요.

        6. **가독성**: 적절한 이모지(📍, ✅, 💡 등)를 활용하고, 중요한 단어는 **굵게** 표시하세요.
        """
        
        main_content = self.client.models.generate_content(model=self.model_complex, contents=prompt).text

        # 모든 출처 정리 (원문 뉴스에서 가져옴)
        sources_footer = "\n\n---\n**참고 자료 및 출처**\n\n" + "\n".join([f"- [{n['title']}]({n['link']}) ({n['source']})" for n in theme_info['news_items']])
        
        return main_content + sources_footer

    def save_post(self, content, filename):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        target_dirs = [
            os.path.join(project_root, "blog/src/content/blog"),
            os.path.join(project_root, "content/posts")
        ]
        
        for base_dir in target_dirs:
            os.makedirs(base_dir, exist_ok=True)
            path = os.path.join(base_dir, filename)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Saved: {path}")

    def review_post(self, content):
        if "참고 자료 및 출처" not in content: return "FAIL. 출처 누락"
        return "PASS"
