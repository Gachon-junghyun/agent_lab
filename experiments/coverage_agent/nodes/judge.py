# FILE: experiments/coverage_agent/nodes/judge.py
import json
from core.ai.base import call_llm
from core.agent.utils import parse_json
from experiments.coverage_agent.state import CoverageState
from experiments.coverage_agent.prompts import JUDGE_SYSTEM


def run_judge(state: CoverageState, llm) -> CoverageState:
    """체크리스트 + 요약 → pass/fail + 누락 항목 + fix 지시"""
    checklist_str = json.dumps(state.checklist, ensure_ascii=False, indent=2)
    coverage_str = json.dumps(state.coverage_map, ensure_ascii=False, indent=2)

    system = JUDGE_SYSTEM
    user = (
        f"사용자 목표: {state.user_goal}\n\n"
        f"체크리스트:\n{checklist_str}\n\n"
        f"생성된 요약:\n{state.draft_summary}\n\n"
        f"coverage_map:\n{coverage_str}"
    )

    state.log("Judge 실행 중...")
    raw = call_llm(llm, system, user)
    parsed = parse_json(raw)

    state.trace("judge", f"[SYSTEM]\n{system}\n\n[USER]\n{user}", raw, parsed)
    state.judge_result = parsed

    verdict = parsed.get("verdict", "fail")
    score = parsed.get("coverage_score", 0.0)
    missing = len(parsed.get("missing_items", []))
    state.log(f"Judge 결과: {verdict.upper()} (score={score:.2f}, 누락={missing}개)")
    return state
