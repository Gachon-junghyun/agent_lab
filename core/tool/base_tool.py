# FILE: core/tool/base_tool.py
# @core-candidate: BaseTool / AgentTool, 2026-04, 모든 툴의 추상 기반 클래스
from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    name: str = ""
    description: str = ""

    @abstractmethod
    def run(self, *args, **kwargs) -> Any:
        ...

    def spec(self) -> dict:
        return {"name": self.name, "description": self.description}


class AgentTool(BaseTool, ABC):
    """
    CoverageState + LLM을 받아 state를 반환하는 에이전트 노드 툴.

    run()이 호출되면:
      1. state.active_guideline = guideline  (call_llm이 system에 자동 주입)
      2. _run(state, llm) 실행
      3. state.active_guideline 초기화
    """

    def run(self, state: Any, llm: Any, guideline: str = "") -> Any:
        state.active_guideline = guideline
        try:
            return self._run(state, llm)
        finally:
            state.active_guideline = ""

    @abstractmethod
    def _run(self, state: Any, llm: Any) -> Any:
        """서브클래스에서 노드 함수를 호출."""
        ...
