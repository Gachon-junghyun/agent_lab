# FILE: core/tool/base_tool.py
# @core-candidate: BaseTool, 2026-04, 모든 툴의 추상 기반 클래스
from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    name: str = ""
    description: str = ""

    @abstractmethod
    def run(self, *args, **kwargs) -> Any:
        """툴 실행. 서브클래스에서 시그니처 정의."""
        ...

    def spec(self) -> dict:
        return {"name": self.name, "description": self.description}


class AgentTool(BaseTool, ABC):
    """CoverageState + LLM을 받아 state를 반환하는 에이전트 노드 툴."""

    @abstractmethod
    def run(self, state: Any, llm: Any, guideline: str = "") -> Any:
        """state를 받아 수정된 state를 반환."""
        ...
