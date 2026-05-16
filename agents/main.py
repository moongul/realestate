import os
import re
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from researcher import RealEstateResearcher
from writer import BlogWriter
from specialists import DataAnalyst, PersonaEditor, SEOOptimizer
from market_agents import SeoulMarketCollector, MarketWriter
from db_manager import RealEstateDBManager
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

class AgentState(TypedDict):
    category: str # 'analysis' or 'market'
    topics: List[dict]
    selected_theme: dict
    analyzed_data: dict
    market_data: dict
    draft_post: str
    edited_post: str
    seo_metadata: dict
    final_post: str
    filename: str
    review_result: str
    retry_count: int

def research_node(state: AgentState):
    if state.get("category") != "analysis": return state
    print("\n[Node: Researcher] 최신 트렌드 분석 및 테마 선정 중...")
    researcher = RealEstateResearcher()
    raw_topics = researcher.fetch_multi_source_topics()
    
    if not raw_topics:
        print("새로운 뉴스가 부족합니다.")
        return state

    selected_theme = researcher.group_and_select_best_theme(raw_topics)
    print(f"선정된 테마: {selected_theme['title']} ({len(selected_theme['news_items'])}개의 출처 취합)")
    return {"topics": raw_topics, "selected_theme": selected_theme, "retry_count": 0}

def market_collect_node(state: AgentState):
    if state.get("category") != "market": return state
    print("\n[Node: Market Collector] 최신 실거래 데이터 업데이트 및 통계 추출 중...")
    
    db = RealEstateDBManager()
    
    # 1. 오늘 기준 최신 데이터 업데이트 (이번 달과 지난 달 데이터 동기화)
    current_ym = datetime.now().strftime("%Y%m")
    prev_ym = (datetime.now().replace(day=1) - timedelta(days=1)).strftime("%Y%m")
    
    seoul_districts = ["11110", "11140", "11170", "11200", "11215", "11230", "11260", "11290", "11305", "11320", "11350", "11380", "11410", "11440", "11470", "11500", "11530", "11545", "11560", "11590", "11620", "11650", "11680", "11710", "11740"]
    
    for ym in [prev_ym, current_ym]:
        for code in seoul_districts:
            db.fetch_and_save_trades(code, ym)
    
    # 2. 어제 날짜 통계 계산
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    db.calculate_daily_stats(yesterday)
    
    # 3. 데이터 분석 에이전트 실행
    collector = SeoulMarketCollector()
    market_data = collector.fetch_current_prices()
    return {"market_data": market_data}

def analyze_node(state: AgentState):
    if state.get("category") != "analysis": return state
    if not state.get("selected_theme"): return state
    analyst = DataAnalyst()
    analyzed_data = analyst.analyze(state["selected_theme"])
    return {"analyzed_data": analyzed_data}

def write_node(state: AgentState):
    current_retry = state.get("retry_count", 0)
    print(f"\n[Node: Writer] 리포트 집필 중... (시도: {current_retry + 1})")
    
    if state.get("category") == "analysis":
        if not state.get("analyzed_data"): return state
        writer = BlogWriter()
        draft_post = writer.generate_post(state['selected_theme'], state['analyzed_data'])
    else:
        if not state.get("market_data"): return state
        writer = MarketWriter()
        draft_post = writer.generate_briefing(state['market_data'])
        
    return {"draft_post": draft_post, "retry_count": current_retry + 1}

def edit_node(state: AgentState):
    if not state.get("draft_post"): return state
    editor = PersonaEditor()
    edited_post = editor.edit(state["draft_post"])
    return {"edited_post": edited_post}

def seo_node(state: AgentState):
    if not state.get("edited_post"): return state
    seo = SEOOptimizer()
    
    theme_title = state["selected_theme"]["title"] if state["category"] == "analysis" else f"서울 {state['market_data'].get('date')} 시세 브리핑"
    
    metadata = seo.optimize(state["edited_post"], theme_title)
    
    # 제목 및 파일명 준비
    title_clean = str(metadata.get('title', theme_title)).replace('"', "'")
    desc_clean = str(metadata.get('description', '')).replace('"', "'")
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    slug_title = re.sub(r'[^a-zA-Z0-9가-힣\s]', '', title_clean)
    slug = "-".join(slug_title.split()[:4])
    filename_base = f"{date_str}-{slug}"
    
    pub_date = datetime.now().strftime("%Y-%m-%d")

    # 이미지는 이제 사용하지 않음
    frontmatter = f"""---
title: "{title_clean}"
description: "{desc_clean}"
category: "{state['category']}"
pubDate: {pub_date}
---"""
    final_post = f"{frontmatter}\n\n{state['edited_post']}"
    
    return {"seo_metadata": metadata, "final_post": final_post, "filename": f"{filename_base}.md"}

def review_node(state: AgentState):
    if not state.get("final_post"): return state
    print("\n[Node: Reviewer] 최종 검수 중...")
    writer = BlogWriter()
    result = writer.review_post(state['final_post'])
    print(f"--- 검수 결과: {result} ---")
    return {"review_result": result}

def should_rewrite(state: AgentState):
    result = state.get("review_result", "FAIL")
    if result.startswith("PASS") or state.get("retry_count", 0) >= 2:
        return "publish"
    return "write"

def publish_node(state: AgentState):
    if not state.get("final_post"): return state
    print(f"\n[Node: Publisher] 최종 결과 저장 중...")
    writer = BlogWriter()
    writer.save_post(state['final_post'], state['filename'])
    
    if state["category"] == "analysis":
        researcher = RealEstateResearcher()
        researcher.save_to_history(state['selected_theme']['news_items'])
    return state

def build_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("research", research_node)
    workflow.add_node("market_collect", market_collect_node)
    workflow.add_node("analyze", analyze_node)
    workflow.add_node("write", write_node)
    workflow.add_node("edit", edit_node)
    workflow.add_node("seo", seo_node)
    workflow.add_node("review", review_node)
    workflow.add_node("publish", publish_node)

    # Entry decision
    def route_start(state: AgentState):
        return state.get("category", "analysis")

    workflow.set_conditional_entry_point(route_start, {"analysis": "research", "market": "market_collect"})
    
    workflow.add_edge("research", "analyze")
    workflow.add_edge("analyze", "write")
    
    workflow.add_edge("market_collect", "write")
    
    workflow.add_edge("write", "edit")
    workflow.add_edge("edit", "seo")
    workflow.add_edge("seo", "review")
    workflow.add_conditional_edges("review", should_rewrite, {"publish": "publish", "write": "write"})
    workflow.add_edge("publish", END)
    return workflow.compile()

def run_workflow(category: str):
    print(f"\n--- {category.upper()} 워크플로우 실행 ---")
    app = build_graph()
    initial_state = {
        "category": category,
        "topics": [], "selected_theme": {}, "analyzed_data": {}, "market_data": {},
        "draft_post": "", "edited_post": "", "seo_metadata": {}, 
        "final_post": "", "filename": "", "review_result": "", "retry_count": 0
    }
    app.invoke(initial_state)

def main():
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "both"
    
    if mode in ["analysis", "both"]:
        run_workflow("analysis")
    
    if mode in ["market", "both"]:
        run_workflow("market")
        
    print("\n--- 전체 워크플로우 종료 ---")

if __name__ == "__main__":
    main()
