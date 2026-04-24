# FILE: experiments/coverage_agent/nodes/extractor.py
from core.ai.base import call_llm
from core.agent.utils import parse_json
from experiments.coverage_agent.state import CoverageState
from experiments.coverage_agent.prompts import EXTRACTOR_SYSTEM


def run_extractor(state: CoverageState, llm) -> CoverageState:
    """문서 전체 → coverage checklist JSON"""
    system = EXTRACTOR_SYSTEM
    user = f"사용자 목표: {state.user_goal}\n\n문서:\n{state.docs_as_text()}"

    state.log("Extractor 실행 중...")
    raw = call_llm(llm, system, user)
    parsed = parse_json(raw)

    state.trace("extractor", f"[SYSTEM]\n{system}\n\n[USER]\n{user}", raw, parsed)
    state.checklist = parsed.get("coverage_items", [])

    high = sum(1 for c in state.checklist if c.get("priority") == "high")
    state.log(f"체크리스트 추출: {len(state.checklist)}개 항목 (high: {high}개)")
    return state
