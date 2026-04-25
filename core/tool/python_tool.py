# FILE: core/tool/python_tool.py
# @core-candidate: PythonTool, 2026-04, LLM 없이 Python 코드로 결정적 동작하는 도구 기반 클래스
"""
PythonTool — 결정적(Deterministic) 도구 기반 클래스

사용 이유:
  LLM은 체크리스트 누락 여부처럼 완전성(completeness)이 필요한 작업에서
  항목을 빠뜨릴 수 있다. 이런 경우 Python 코드로 직접 검사하면 누락 없이
  모든 항목을 처리할 수 있다.

사용 예:
  - coverage_map에서 누락된 high priority 항목 집계
  - JSON 구조 유효성 검사
  - 체크리스트 항목이 요약에 키워드 수준으로 포함됐는지 전수 검사
"""
from abc import abstractmethod
from typing import Any

from core.tool.base_tool import BaseTool


class PythonTool(BaseTool):
    """
    Python 함수 기반 결정적 도구.

    run()은 LLM을 호출하지 않으며, _execute()에 구현된 Python 로직만 실행한다.
    state를 받아 state를 돌려주는 AgentTool과 달리,
    임의의 입력을 받아 임의의 출력을 돌려주는 범용 형태다.
    """

    @abstractmethod
    def _execute(self, *args, **kwargs) -> Any:
        """서브클래스에서 실제 Python 로직 구현."""
        ...

    def run(self, *args, **kwargs) -> Any:
        return self._execute(*args, **kwargs)


class AgentPythonTool(PythonTool):
    """
    CoverageState를 받아 Python 코드로 분석 후 state를 수정해 돌려주는 도구.

    LLM 없이 state 필드를 직접 읽고 쓰기 때문에 완전성 보장이 필요한
    집계·검증·정렬 작업에 적합하다.
    """

    def run(self, state: Any, **kwargs) -> Any:  # type: ignore[override]
        return self._execute(state, **kwargs)

    @abstractmethod
    def _execute(self, state: Any, **kwargs) -> Any: ...
