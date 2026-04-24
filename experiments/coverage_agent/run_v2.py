# FILE: experiments/coverage_agent/run_v2.py
"""
ToolRegistry 기반 오케스트레이터 버전.

사용법:
    python -m experiments.coverage_agent.run_v2 --goal "LLM 파인튜닝 개념 정리" --model gemini
"""
import argparse
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_COVERAGE_DIR = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from core.ai import get_llm
from core.agent.ingest import load_documents
from core.tool.registry import ToolRegistry
from core.orchestrator import OrchestratorHarness
from core.ui import show_flow

from experiments.coverage_agent.state import CoverageState
from experiments.coverage_agent.tools import (
    PlannerTool, ExtractorTool, SummarizerTool, JudgeTool, AuditorTool,
)
from experiments.coverage_agent.harness import save_run_log


def build_llm(args):
    if args.model == "gemini":
        return get_llm("gemini", model_name=args.gemini_model)
    if args.model == "ollama":
        return get_llm("ollama", model_name=args.ollama_model)
    if args.model == "deepseek":
        return get_llm("deepseek", model_name=args.deepseek_model)
    raise ValueError(f"알 수 없는 모델: {args.model}")


def main():
    parser = argparse.ArgumentParser(description="Coverage Agent v2 — ToolRegistry 기반")
    parser.add_argument("--goal", required=True)
    parser.add_argument("--model", default="gemini", choices=["gemini", "ollama", "deepseek"])
    parser.add_argument("--data-dir", default=os.path.join(_COVERAGE_DIR, "data"))
    parser.add_argument("--log-dir", default=os.path.join(_COVERAGE_DIR, "logs"))
    parser.add_argument("--max-retries", type=int, default=2)
    parser.add_argument("--no-gui", action="store_true")
    parser.add_argument("--gemini-model", default="gemini-2.5-flash")
    parser.add_argument("--ollama-model", default="llama3")
    parser.add_argument("--deepseek-model", default="deepseek-chat")
    args = parser.parse_args()

    llm = build_llm(args)
    docs = load_documents(args.data_dir)

    # ── ToolRegistry 구성 ─────────────────────────────────────────────
    registry = ToolRegistry()
    registry.register_all([
        PlannerTool(),
        ExtractorTool(),
        SummarizerTool(),
        JudgeTool(),
        AuditorTool(),
    ])

    # ── 초기 가이드라인 ───────────────────────────────────────────────
    initial_guidelines = {
        "planner":    "작업 유형을 명확히 분류하고 subtask는 3개 이하로 설정해라.",
        "extractor":  "우선순위 high 항목 위주로 추출하고 중복을 제거해라.",
        "summarizer": "체크리스트 항목을 빠짐없이 커버하되 3000자 이내로 작성해라.",
        "judge":      "coverage_score 0.8 이상이어야 pass로 판단해라.",
        "auditor":    "judge pass이고 사실 오류가 없으면 approve를 반환해라.",
    }

    # ── Harness 실행 ──────────────────────────────────────────────────
    harness = OrchestratorHarness(
        registry=registry,
        llm=llm,
        initial_guidelines=initial_guidelines,
        max_steps=12,
        max_retries=args.max_retries,
    )

    state = CoverageState(
        user_goal=args.goal,
        documents=docs,
        max_retries=args.max_retries,
    )
    state = harness.run(state)

    # ── 결과 출력 ─────────────────────────────────────────────────────
    print("\n" + "=" * 54)
    print("최종 결과:")
    print("=" * 54)
    if state.final_output:
        print(state.final_output)
    else:
        print(f"[audit 결정: {(state.audit_result or {}).get('release_decision', '없음')}]")
        print(state.draft_summary or "(출력 없음)")

    save_run_log(state, log_dir=args.log_dir)

    if not args.no_gui:
        show_flow(state)


if __name__ == "__main__":
    main()
