# FILE: core/tool/summarize_tool.py
# @core-candidate: SummarizeTool, 2026-04, guideline 주입 요약 툴
from typing import Any

from core.ai.base import call_llm
from core.tool.base_tool import BaseTool

_DEFAULT_GUIDELINE = "주어진 텍스트를 핵심만 간결하게 요약하라. 불필요한 반복 없이 명확하게 작성해라."


class SummarizeTool(BaseTool):
    name = "summarize"
    description = (
        "제공된 텍스트를 가이드라인에 따라 요약한다. "
        "input: 요약할 텍스트."
    )

    def __init__(self, llm: Any) -> None:
        self._llm = llm

    def run(self, input: str, guideline: str = "") -> str:
        system = guideline.strip() or _DEFAULT_GUIDELINE
        return call_llm(self._llm, system=system, user=input)
