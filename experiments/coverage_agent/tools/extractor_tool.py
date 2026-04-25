# FILE: experiments/coverage_agent/tools/extractor_tool.py
from typing import Any
from core.tool.base_tool import AgentTool
from experiments.coverage_agent.nodes.extractor import run_extractor


class ExtractorTool(AgentTool):
    name = "extractor"
    description = (
        "문서 전체를 청크 단위로 읽고 coverage checklist 항목을 누락 없이 추출한다. "
        "task_plan 수립 후 실행한다."
    )

    def _run(self, state: Any, llm: Any) -> Any:
        return run_extractor(state, llm)
