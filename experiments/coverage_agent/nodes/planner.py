# FILE: experiments/coverage_agent/nodes/planner.py
from core.ai.base import call_llm
from core.agent.utils import parse_json
from experiments.coverage_agent.state import CoverageState
from experiments.coverage_agent.prompts import PLANNER_SYSTEM


def run_planner(state: CoverageState, llm) -> CoverageState:
    """사용자 목표 + 문서 개요 → task_plan JSON"""
    doc_overview = "\n".join(
        f"- [{d.id}] {d.filename} ({len(d.content):,}자)" for d in state.documents
    ) or "문서 없음"

    system = PLANNER_SYSTEM
    user = f"사용자 목표: {state.user_goal}\n\n제공 문서 목록:\n{doc_overview}"

    state.log("Planner 실행 중...")
    raw = call_llm(llm, system, user)
    parsed = parse_json(raw)

    state.trace("planner", f"[SYSTEM]\n{system}\n\n[USER]\n{user}", raw, parsed)
    state.task_plan = parsed
    state.log(f"작업 유형: {parsed.get('task_type')} | subtask {len(parsed.get('subtasks', []))}개")
    return state
