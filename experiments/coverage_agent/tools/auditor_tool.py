# FILE: experiments/coverage_agent/tools/auditor_tool.py
from typing import Any
from core.tool.base_tool import AgentTool
from experiments.coverage_agent.nodes.auditor import run_auditor


class AuditorTool(AgentTool):
    name = "auditor"
    description = (
        "judge 결과와 최종 요약을 검토해 approve / revise / escalate를 결정한다. "
        "모든 작업의 마지막 단계에서 실행한다."
    )

    def run(self, state: Any, llm: Any, guideline: str = "") -> Any:
        return run_auditor(state, llm)
