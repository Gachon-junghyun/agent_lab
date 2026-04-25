# FILE: experiments/coverage_agent/nodes/summarizer.py
import json
from core.ai.base import call_llm
from experiments.coverage_agent.state import CoverageState
from experiments.coverage_agent.prompts import SUMMARIZER_SYSTEM
from experiments.coverage_agent.utils import parse_coverage_response


def run_summarizer(state: CoverageState, llm) -> CoverageState:
    checklist_str = json.dumps(state.checklist, ensure_ascii=False, indent=2)
    revision_hint = ""
    if state.judge_result and state.judge_result.get("revision_plan"):
        plans = "\n".join(f"- {p}" for p in state.judge_result["revision_plan"])
        revision_hint = f"\n\n[재시도 지시 — 아래 항목을 반드시 보완하라]\n{plans}"

    user = (
        f"사용자 목표: {state.user_goal}\n\n"
        f"체크리스트:\n{checklist_str}\n\n"
        f"문서:\n{state.docs_as_text()}{revision_hint}"
    )

    state.log(f"Summarizer 실행 중... (시도 {state.retry_count + 1}회)")
    raw = call_llm(llm, SUMMARIZER_SYSTEM, user, guideline=getattr(state, "active_guideline", ""))
    summary, coverage_map = parse_coverage_response(raw)

    state.trace("summarizer", f"[SYSTEM]\n{SUMMARIZER_SYSTEM}\n\n[USER]\n{user}", raw,
                {"summary": summary, "coverage_map": coverage_map})
    state.draft_summary = summary
    state.coverage_map = coverage_map
    included = len(coverage_map.get("included_items", []))
    omitted = len(coverage_map.get("omitted_items", []))
    state.log(f"요약 완료 — 포함 {included}개 / 누락 {omitted}개")
    return state
