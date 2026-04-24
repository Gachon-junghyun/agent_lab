# FILE: experiments/coverage_agent/nodes/verifier.py
from core.ai.base import call_llm
from core.agent.utils import parse_json
from experiments.coverage_agent.state import CoverageState
from experiments.coverage_agent.prompts import VERIFIER_SYSTEM


def run_verifier(state: CoverageState, llm) -> CoverageState:
    """요약 → atomic claim 분해 + 문서 기반 사실 검증"""
    system = VERIFIER_SYSTEM
    user = (
        f"사용자 목표: {state.user_goal}\n\n"
        f"검증할 요약:\n{state.draft_summary}\n\n"
        f"근거 문서:\n{state.docs_as_text()}"
    )

    state.log("Verifier 실행 중...")
    raw = call_llm(llm, system, user)
    parsed = parse_json(raw)

    state.trace("verifier", f"[SYSTEM]\n{system}\n\n[USER]\n{user}", raw, parsed)
    state.verify_result = parsed

    claims = parsed.get("claims", [])
    unsupported = [c for c in claims if c.get("status") == "unsupported"]
    state.log(f"검증 완료 — 총 {len(claims)}개 claim, 미검증 {len(unsupported)}개")
    return state
