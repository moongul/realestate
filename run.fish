#!/usr/bin/fish

# 가상환경 활성화 (uv 사용 시 .venv/bin/activate.fish)
source agents/.venv/bin/activate.fish

# 메인 에이전트 실행
python3 agents/main.py both
