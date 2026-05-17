import subprocess
import json
import re
import os

class OpenCodeHelper:
    @staticmethod
    def run(agent_name, inputs):
        """
        opencode run --agent {agent_name} "{prompt}" 명령어를 실행하여 결과를 반환함.
        inputs: .md 파일의 변수들을 채울 딕셔너리
        """
        # 입력을 문자열로 변환 (JSON 형태 또는 줄바꿈 포함 텍스트)
        # .md 파일의 {variable} 형식을 채우기 위해 프롬프트 구성
        prompt_parts = []
        for key, value in inputs.items():
            if isinstance(value, (dict, list)):
                val_str = json.dumps(value, ensure_ascii=False)
            else:
                val_str = str(value)
            prompt_parts.append(f"{key}: {val_str}")
        
        full_prompt = "\n".join(prompt_parts)
        
        print(f"[OpenCode] Agent '{agent_name}' 호출 중...")
        
        try:
            # opencode run --agent {name} "{prompt}"
            cmd = ["opencode", "run", "--agent", agent_name, full_prompt]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
            
            if result.returncode != 0:
                print(f"!! OpenCode 실행 오류: {result.stderr}")
                return None
            
            response = result.stdout.strip()
            # 디버깅을 위한 원문 전체 출력
            print(f"========== [OpenCode] {agent_name} 응답 원문 (길이: {len(response)}) ==========\n{response}\n=======================================================")
            return response
            
        except Exception as e:
            print(f"!! OpenCode 호출 예외 발생: {e}")
            return None

    @staticmethod
    def parse_json(text):
        """응답 텍스트에서 JSON 추출 및 파싱"""
        if not text: return None
        
        # 마크다운 코드 블록 명시적 제거
        text_clean = text.strip()
        if text_clean.startswith("```json"):
            text_clean = text_clean[7:]
        elif text_clean.startswith("```"):
            text_clean = text_clean[3:]
            
        if text_clean.endswith("```"):
            text_clean = text_clean[:-3]
            
        text_clean = text_clean.strip()
        
        try:
            return json.loads(text_clean)
        except Exception as e1:
            try:
                # 정규식으로 {} 추출 시도
                json_match = re.search(r'\{.*\}', text_clean, re.DOTALL)
                if json_match:
                    extracted = json_match.group()
                    return json.loads(extracted)
                else:
                    print(f"!! JSON 패턴을 찾을 수 없습니다.")
                    return None
            except Exception as e2:
                print(f"!! JSON 파싱 오류 1: {e1}")
                print(f"!! JSON 파싱 오류 2: {e2}")
                print(f"!! 파싱 시도한 텍스트 전체:\n{text_clean}")
                return None
