"""
OrchestratorHarness 기반 실행 (ReAct + 시맨틱 툴 탐색)

사용법:
    python -m experiments.coverage_agent.run_orch --goal "llm 파인튜닝 개념 정리"
    python -m experiments.coverage_agent.run_orch --goal "..." --model deepseek

고정 파이프라인(run.py)과의 차이:
    run.py      → planner→extractor→summarizer→judge→...  순서 고정
    run_orch.py → OrchestratorHarness가 매 스텝마다 어떤 툴을 쓸지 스스로 결정
"""
import argparse
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_DIR = os.path.dirname(os.path.abspath(__file__))
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


def main():
    parser = argparse.ArgumentParser(description="Coverage Agent — OrchestratorHarness 모드")
    parser.add_argument("--goal", required=True)
    parser.add_argument("--model", default="gemini", choices=["gemini", "ollama", "deepseek"])
    parser.add_argument("--data-dir", default=os.path.join(_DIR, "data"))
    parser.add_argument("--log-dir", default=os.path.join(_DIR, "logs"))
    parser.add_argument("--max-retries", type=int, default=2)
    parser.add_argument("--no-gui", action="store_true")
    parser.add_argument("--gemini-model", default="gemini-2.5-flash")
    parser.add_argument("--ollama-model", default="llama3")
    parser.add_argument("--deepseek-model", default="deepseek-chat")
    args = parser.parse_args()

    llm = get_llm(args.model, model_name=getattr(args, f"{args.model}_model"))
    docs = load_documents(args.data_dir)
    print(f"[run_orch] 모델: {args.model} | 문서: {len(docs)}개")

    registry = ToolRegistry()
    registry.register_all([
        PlannerTool(), ExtractorTool(), SummarizerTool(), JudgeTool(), AuditorTool(),
    ])

    harness = OrchestratorHarness(
        registry=registry,
        llm=llm,
        initial_guidelines={
            "planner":    "작업 유형을 명확히 분류하고 subtask는 3개 이하로 설정해라.",
            "extractor":  "우선순위 high 항목 위주로 추출하고 중복을 제거해라.",
            "summarizer": "체크리스트 항목을 빠짐없이 커버하되 3000자 이내로 작성해라.",
            "judge":      "coverage_score 0.8 이상이어야 pass로 판단해라.",
            "auditor":    "judge pass이고 사실 오류가 없으면 approve를 반환해라.",
        },
        max_steps=12,
        max_retries=args.max_retries,
    )

    state = CoverageState(user_goal=args.goal, documents=docs, max_retries=args.max_retries)
    state = harness.run(state)

    print("\n" + "=" * 54)
    print("최종 결과:")
    print("=" * 54)
    print(state.final_output or state.draft_summary or "(출력 없음)")

    save_run_log(state, log_dir=args.log_dir)
    if not args.no_gui:
        show_flow(state)


if __name__ == "__main__":
    main()
