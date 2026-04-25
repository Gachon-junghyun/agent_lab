# FILE: experiments/coverage_agent/tools/judge_tool.py
from typing import Any
from core.tool.base_tool import AgentTool
from experiments.coverage_agent.nodes.judge import run_judge


class JudgeTool(AgentTool):
    name = "judge"
    description = (
        "checklist 대비 draft_summary의 coverage를 평가해 pass/fail verdict와 "
        "누락 항목, revision_plan을 반환한다. summarizer 실행 후 반드시 호출한다."
    )

    def _run(self, state: Any, llm: Any) -> Any:
        return run_judge(state, llm)
