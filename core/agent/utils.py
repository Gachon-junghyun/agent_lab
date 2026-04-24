# FILE: core/agent/utils.py
# @core-candidate: parse_json, 2026-04, LLM 응답 JSON 파싱 유틸
import json
import re
from typing import Any, Dict


def parse_json(text: str) -> Dict[str, Any]:
    """LLM 응답에서 JSON 추출 (마크다운 코드블록 포함)"""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    raise ValueError(f"JSON 파싱 실패:\n{text[:300]}")
