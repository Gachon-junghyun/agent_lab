# FILE: experiments/coverage_agent/harness.py
import json
import os
from datetime import datetime
from typing import Any

from experiments.coverage_agent.state import CoverageState
from experiments.coverage_agent.nodes.planner import run_planner
from experiments.coverage_agent.nodes.extractor import run_extractor
from experiments.coverage_agent.nodes.summarizer import run_summarizer
from experiments.coverage_agent.nodes.judge import run_judge
from experiments.coverage_agent.nodes.verifier import run_verifier
from experiments.coverage_agent.nodes.auditor import run_auditor


def run_harness(state: CoverageState, llm: Any, run_verify: bool = False) -> CoverageState:
    """plan → extract → summarize/judge loop → [verify] → audit"""
    print(f"\n{'='*50}")
    print(f"[HARNESS] 시작 — 목표: {state.user_goal}")
    print(f"[HARNESS] 문서: {len(state.documents)}개 | 최대 재시도: {state.max_retries}회")
    print(f"{'='*50}\n")

    state = run_planner(state, llm)
    state = run_extractor(state, llm)

    while True:
        state = run_summarizer(state, llm)
        state = run_judge(state, llm)
        if state.judge_result.get("verdict") == "pass":
            state.log("Judge PASS")
            break
        if state.retry_count >= state.max_retries:
            state.log(f"최대 재시도 {state.max_retries}회 초과 — 현재 초안으로 진행")
            break
        state.retry_count += 1
        state.log(f"Judge FAIL → 재시도 {state.retry_count}/{state.max_retries}")

    task_type = (state.task_plan or {}).get("task_type", "summarization")
    if run_verify or task_type in ("research", "hybrid"):
        state = run_verifier(state, llm)

    state = run_auditor(state, llm)

    print(f"\n{'='*50}")
    print(f"[HARNESS] 완료 — {state.status.upper()}")
    print(f"{'='*50}\n")
    return state


def save_run_log(state: CoverageState, log_dir: str = "logs") -> str:
    """logs/YYYYMMDD_HHMMSS/ 에 run_summary.json, node_traces.json, final_output.txt 저장."""
    run_dir = os.path.join(log_dir, datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(run_dir, exist_ok=True)

    with open(os.path.join(run_dir, "run_summary.json"), "w", encoding="utf-8") as f:
        json.dump({
            "user_goal": state.user_goal, "status": state.status,
            "retry_count": state.retry_count, "max_retries": state.max_retries,
            "logs": state.logs, "task_plan": state.task_plan,
            "judge_result": state.judge_result, "verify_result": state.verify_result,
            "audit_result": state.audit_result,
        }, f, ensure_ascii=False, indent=2, default=str)

    with open(os.path.join(run_dir, "node_traces.json"), "w", encoding="utf-8") as f:
        json.dump(state.node_traces, f, ensure_ascii=False, indent=2, default=str)

    with open(os.path.join(run_dir, "final_output.txt"), "w", encoding="utf-8") as f:
        f.write(state.final_output or state.draft_summary or "(출력 없음)")

    print(f"[HARNESS] 로그 저장: {os.path.abspath(run_dir)}")
    return run_dir
