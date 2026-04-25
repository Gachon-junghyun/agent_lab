# FILE: core/tool/factory.py
# @core-candidate: make_llm_tool / make_python_tool, 2026-04, Tool 1줄 생성 팩토리
"""
Tool Factory — 두 가지 성격의 도구를 빠르게 뽑아내는 플랫폼

─────────────────────────────────────────────────────────
[LLM 도구]  make_llm_tool / @llm_tool
  - system 프롬프트를 주면 LLM을 호출하는 BaseTool을 만들어 준다.
  - 텍스트 생성·요약·분류 등 "창의적이어도 되는" 작업에 적합.
  - parse_fn을 넘기면 LLM 응답을 원하는 형태로 후처리 가능.

[Python 도구]  make_python_tool / @python_tool
  - 일반 Python 함수를 BaseTool로 래핑한다.
  - 누락이 없어야 하는 집계·검증·정렬 작업에 적합.
  - LLM을 전혀 사용하지 않으므로 결과가 결정적(deterministic).

─────────────────────────────────────────────────────────
빠른 사용 예:

  # LLM 도구 — 함수형
  keyword_extractor = make_llm_tool(
      name="keyword_extractor",
      description="텍스트에서 핵심 키워드를 추출한다.",
      system_prompt="텍스트에서 핵심 키워드 5개를 JSON 배열로 반환하라.",
  )
  result = keyword_extractor.run(llm, user_text)

  # Python 도구 — 함수형
  gap_checker = make_python_tool(
      name="coverage_gap_checker",
      description="checklist 항목 중 summary에 없는 항목을 반환한다.",
      fn=lambda checklist, summary: [
          item for item in checklist
          if item["point"].lower() not in summary.lower()
      ],
  )
  gaps = gap_checker.run(state.checklist, state.draft_summary)

  # LLM 도구 — 데코레이터
  @llm_tool(name="tone_analyzer", description="글의 어조를 분석한다.",
             system_prompt="글의 어조를 formal/casual/neutral 중 하나로 반환하라.")
  def analyze_tone(response: str) -> str:
      return response.strip()

  # Python 도구 — 데코레이터
  @python_tool(name="high_priority_filter", description="high priority 항목만 필터링한다.")
  def filter_high(checklist):
      return [c for c in checklist if c.get("priority") == "high"]
"""
from typing import Any, Callable, Optional

from core.tool.base_tool import BaseTool
from core.tool.python_tool import PythonTool
from core.ai.base import call_llm


# ─── LLM 도구 팩토리 ──────────────────────────────────────────────────────────

def make_llm_tool(
    name: str,
    description: str,
    system_prompt: str,
    parse_fn: Optional[Callable[[str], Any]] = None,
) -> BaseTool:
    """
    LLM 기반 도구를 1줄로 생성.

    Args:
        name: 도구 이름 (registry 검색 키)
        description: 도구 설명 (registry 시맨틱 검색에 사용)
        system_prompt: LLM system 메시지
        parse_fn: LLM raw 응답을 후처리하는 함수 (기본값: 그대로 반환)

    Returns:
        run(llm, user_text, guideline="") → str | Any
    """
    _parse = parse_fn or (lambda x: x)
    _system = system_prompt

    class _LLMTool(BaseTool):
        def run(self, llm: Any, user_text: str, guideline: str = "") -> Any:  # type: ignore[override]
            raw = call_llm(llm, system=_system, user=user_text, guideline=guideline)
            return _parse(raw)

    _LLMTool.name = name
    _LLMTool.description = description
    return _LLMTool()


def llm_tool(
    name: str,
    description: str,
    system_prompt: str,
) -> Callable:
    """
    LLM 도구 데코레이터.

    데코레이팅된 함수는 parse_fn으로 사용된다.
    함수 시그니처: fn(raw_response: str) -> Any

    사용 예:
        @llm_tool(name="classifier", description="...", system_prompt="...")
        def classify(response: str) -> str:
            return response.strip().lower()
    """
    def decorator(fn: Callable) -> BaseTool:
        return make_llm_tool(
            name=name,
            description=description,
            system_prompt=system_prompt,
            parse_fn=fn,
        )
    return decorator


# ─── Python 도구 팩토리 ───────────────────────────────────────────────────────

def make_python_tool(
    name: str,
    description: str,
    fn: Callable,
) -> PythonTool:
    """
    Python 함수를 PythonTool로 래핑.

    Args:
        name: 도구 이름
        description: 도구 설명
        fn: 실제 로직 함수 (*args, **kwargs 자유롭게 사용)

    Returns:
        run(*args, **kwargs) → fn의 반환값
    """
    _fn = fn

    class _PythonTool(PythonTool):
        def _execute(self, *args, **kwargs) -> Any:
            return _fn(*args, **kwargs)

    _PythonTool.name = name
    _PythonTool.description = description
    return _PythonTool()


def python_tool(name: str, description: str) -> Callable:
    """
    Python 도구 데코레이터.

    데코레이팅된 함수가 그대로 도구의 실행 함수가 된다.

    사용 예:
        @python_tool(name="gap_checker", description="누락 항목을 반환한다.")
        def check_gaps(checklist, summary):
            return [c for c in checklist if c["point"] not in summary]
    """
    def decorator(fn: Callable) -> PythonTool:
        return make_python_tool(name=name, description=description, fn=fn)
    return decorator
