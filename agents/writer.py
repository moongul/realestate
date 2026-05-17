import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()

from opencode_helper import OpenCodeHelper

class BlogWriter:
    def generate_post(self, theme_info, analyzed_data):
        """OpenCode Writer 에이전트를 사용하여 리포트 초안 작성"""
        print(f"[Writer] 리포트 초안 집필 중...")
        
        regional_text = ""
        for r in analyzed_data.get('regional_data', []):
            regional_text += f"- 지역: {r.get('region')}\n  동향: {r.get('trend')}\n  가격정보: {r.get('price_info')}\n  비고: {r.get('note')}\n\n"

        inputs = {
            "theme_title": theme_info['title'],
            "market_vibe": analyzed_data.get('market_vibe', '보합'),
            "key_factors": analyzed_data.get('key_factors', '이슈 없음'),
            "attention_level": analyzed_data.get('attention_level', '관망'),
            "analyzed_data": json.dumps(analyzed_data, ensure_ascii=False),
            "regional_text": regional_text
        }
        
        main_content = OpenCodeHelper.run("writer", inputs)

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
