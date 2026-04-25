# FILE: experiments/coverage_agent/tools/summarizer_tool.py
from typing import Any
from core.tool.base_tool import AgentTool
from experiments.coverage_agent.nodes.summarizer import run_summarizer


class SummarizerTool(AgentTool):
    name = "summarizer"
    description = (
        "checklist와 문서를 기반으로 draft_summary와 coverage_map을 생성한다. "
        "judge 실패 시 revision_plan을 반영해 재실행할 수 있다."
    )

    def _run(self, state: Any, llm: Any) -> Any:
        return run_summarizer(state, llm)
