# FILE: core/agent/utils.py
# @core-candidate: parse_json, 2026-04, LLM 응답 JSON 파싱 유틸
import json
import re
from typing import Any, Dict


_JSON_VALID_ESCAPES = set('"\\/ bfnrt')  # JSON 스펙에서 허용하는 단일 이스케이프


def _sanitize_json_str(s: str) -> str:
    """
    JSON 문자열 토큰 내부의 유효하지 않은 백슬래시 이스케이프를 수정한다.

    정규식은 문자열 내부/외부를 구분하지 못하므로 직접 순회한다.
    JSON 스펙 허용 이스케이프: backslash + " \\ / b f n r t uXXXX
    그 외 backslash+X 는 double-backslash+X 로 치환한다.
    """
    out: list = []
    i = 0
    in_str = False
    while i < len(s):
        ch = s[i]
        if ch == '"' and (i == 0 or s[i - 1] != '\\'):
            in_str = not in_str
            out.append(ch)
            i += 1
        elif ch == '\\' and in_str:
            nxt = s[i + 1] if i + 1 < len(s) else ''
            if nxt in _JSON_VALID_ESCAPES:
                out.append(ch)
                out.append(nxt)
                i += 2
            elif nxt == 'u':
                # \uXXXX 이면 그대로, 아니면 이스케이프
                hex4 = s[i + 2:i + 6]
                if re.fullmatch(r'[0-9a-fA-F]{4}', hex4):
                    out.append(s[i:i + 6])
                    i += 6
                else:
                    out.append('\\\\')
                    i += 1
            else:
                # 유효하지 않은 이스케이프 → 백슬래시를 이스케이프
                out.append('\\\\')
                i += 1
        else:
            out.append(ch)
            i += 1
    return ''.join(out)


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
