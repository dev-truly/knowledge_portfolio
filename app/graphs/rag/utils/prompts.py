import os
from pathlib import Path

def load_prompt(filename: str) -> str:
    """매번 호출될 때마다 파일 시스템에서 프롬프트를 읽어옵니다. (Hot-reload 가능)"""
    prompt_path = Path("app/graphs/prompts") / filename
    if not prompt_path.exists():
        raise FileNotFoundError(f"프롬프트 파일을 찾을 수 없습니다: {prompt_path}")
    
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()
