# FILE: experiments/coverage_agent/tools/planner_tool.py
from typing import Any
from core.tool.base_tool import AgentTool
from experiments.coverage_agent.nodes.planner import run_planner


class PlannerTool(AgentTool):
    name = "planner"
    description = (
        "사용자 목표와 문서 목록을 분석해 task_type과 subtask 목록을 담은 "
        "task_plan을 수립한다. 가장 먼저 실행해야 한다."
    )

    def _run(self, state: Any, llm: Any) -> Any:
        return run_planner(state, llm)
