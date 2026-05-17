import os
import json
from opencode_helper import OpenCodeHelper

class DataAnalyst:
    def analyze(self, theme_info):
        """OpenCode Analyst 에이전트를 사용하여 데이터 추출"""
        print(f"[Data Analyst] {len(theme_info['news_items'])}개의 뉴스에서 핵심 수치 추출 중...")
        
        inputs = {
            "theme_title": theme_info['title'],
            "sources_text": "\n\n".join([f"제목: {n['title']}\n요약: {n['summary']}" for n in theme_info['news_items']])
        }
        
        response = OpenCodeHelper.run("analyst", inputs)
        data = OpenCodeHelper.parse_json(response)
        
        if not data:
            return {
                "market_vibe": "정보 부족", "key_factors": "정보 부족", "attention_level": "관망",
                "regional_data": [], "expert_insight": "분석 데이터를 생성할 수 없습니다."
            }
        return data

class PersonaEditor:
    def edit(self, draft_text):
        """OpenCode Editor 에이전트를 사용하여 톤앤매너 교정"""
        print(f"[Persona Editor] 브랜드 톤앤매너 적용 및 교정 중...")
        
        inputs = {"draft_text": draft_text}
        return OpenCodeHelper.run("editor", inputs)

class SEOOptimizer:
    def optimize(self, final_text, theme_title):
        """OpenCode SEO 에이전트를 사용하여 메타데이터 생성"""
        print(f"[SEO Optimizer] 검색 엔진 최적화 메타데이터 추출 중...")
        
        inputs = {
            "text_preview": final_text[:800],
            "theme_title": theme_title
        }
        
        response = OpenCodeHelper.run("seo", inputs)
        data = OpenCodeHelper.parse_json(response)
        
        if not data:
            return {"title": theme_title, "description": theme_title}
        return data
