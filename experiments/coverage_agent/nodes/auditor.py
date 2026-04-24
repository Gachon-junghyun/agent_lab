# FILE: experiments/coverage_agent/nodes/auditor.py
import json
from core.ai.base import call_llm
from core.agent.utils import parse_json
from experiments.coverage_agent.state import CoverageState
from experiments.coverage_agent.prompts import AUDITOR_SYSTEM


def run_auditor(state: CoverageState, llm) -> CoverageState:
    """최종 산출물 릴리스 게이트 — approve / revise / escalate"""
    judge_str = json.dumps(state.judge_result, ensure_ascii=False, indent=2)
    verify_str = json.dumps(state.verify_result, ensure_ascii=False, indent=2) if state.verify_result else "검증 생략"

    system = AUDITOR_SYSTEM
    user = (
        f"사용자 목표: {state.user_goal}\n\n"
        f"최종 요약:\n{state.draft_summary}\n\n"
        f"Judge 결과:\n{judge_str}\n\n"
        f"Verifier 결과:\n{verify_str}"
    )

    state.log("Auditor 실행 중...")
    raw = call_llm(llm, system, user)
    parsed = parse_json(raw)

    state.trace("auditor", f"[SYSTEM]\n{system}\n\n[USER]\n{user}", raw, parsed)
    state.audit_result = parsed

    decision = parsed.get("release_decision", "revise")
    state.log(f"Audit 결정: {decision.upper()}")

    if decision == "approve":
        state.final_output = state.draft_summary
        state.status = "done"
    else:
        state.log(f"수정 필요 항목: {parsed.get('must_fix', [])}")
        state.status = "failed"

    return state
