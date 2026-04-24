# FILE: core/agent/utils.py
# @core-candidate: parse_json, 2026-04, LLM 응답 JSON 파싱 유틸
import json
import re
from typing import Any, Dict


def _sanitize_json_str(s: str) -> str:
    """유효하지 않은 JSON 이스케이프를 이중 백슬래시로 교체."""
    # \uXXXX 형식이 아닌 \u 먼저 처리
    s = re.sub(r'\\u(?![0-9a-fA-F]{4})', r'\\\\u', s)
    # 나머지 유효하지 않은 이스케이프 처리 (\", \\, \/, \b, \f, \n, \r, \t 제외)
    s = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', s)
    return s


def _extract_balanced(text: str) -> str:
    """중괄호 균형을 맞춰 JSON 객체 문자열 추출. 중첩 객체 지원."""
    start = text.find('{')
    if start == -1:
        raise ValueError("JSON 객체({)를 찾을 수 없음")
    depth = 0
    in_str = False
    esc = False
    for i, ch in enumerate(text[start:], start):
        if esc:
            esc = False
            continue
        if ch == '\\' and in_str:
            esc = True
            continue
        if ch == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    raise ValueError("JSON 닫는 괄호(})를 찾을 수 없음")


def parse_json(text: str) -> Dict[str, Any]:
    """LLM 응답에서 JSON 추출. 마크다운 코드블록 및 중첩 객체 지원."""
    text = text.strip()
    raw = _extract_balanced(text)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return json.loads(_sanitize_json_str(raw))
