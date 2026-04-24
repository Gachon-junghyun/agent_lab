# FILE: experiments/coverage_agent/tools/extractor_tool.py
from typing import Any
from core.tool.base_tool import AgentTool
from experiments.coverage_agent.nodes.extractor import run_extractor


class ExtractorTool(AgentTool):
    name = "extractor"
    description = (
        "문서 전체를 읽고 사용자 목표와 관련된 coverage checklist 항목을 추출한다. "
        "task_plan이 수립된 후 실행한다."
    )

    def run(self, state: Any, llm: Any, guideline: str = "") -> Any:
        return run_extractor(state, llm)
