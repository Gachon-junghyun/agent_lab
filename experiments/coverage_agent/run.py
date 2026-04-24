"""
사용법 (AGENT/ 루트에서 실행):
    python -m experiments.coverage_agent.run --goal "LLM 파인튜닝 개념 및 방법 요약" --model gemini 
    python -m experiments.coverage_agent.run --goal "..." --model deepseek --deepseek-model deepseek-reasoner
    python -m experiments.coverage_agent.run --goal "..." --model ollama --ollama-model qwen2.5:7b
    python -m experiments.coverage_agent.run --goal "..." --model gemini --verify

또는 PYTHONPATH 설정 후 직접 실행:
    PYTHONPATH=/path/to/AGENT python experiments/coverage_agent/run.py --goal "..."
"""
import argparse
import os
import sys

# AGENT/ 루트를 sys.path에 추가 (PYTHONPATH 미설정 환경 대비)
_AGENT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_COVERAGE_DIR = os.path.dirname(os.path.abspath(__file__))  # coverage_agent/ 절대경로
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)

from core.ai import get_llm
from core.agent.ingest import load_documents
from core.ui import show_flow
from experiments.coverage_agent.state import CoverageState
from experiments.coverage_agent.harness import run_harness, save_run_log


def build_llm(args):
    if args.model == "gemini":
        return get_llm("gemini", model_name=args.gemini_model)
    if args.model == "ollama":
        return get_llm("ollama", model_name=args.ollama_model)
    if args.model == "deepseek":
        return get_llm("deepseek", model_name=args.deepseek_model)
    raise ValueError(f"알 수 없는 모델: {args.model}")


def main():
    parser = argparse.ArgumentParser(description="Coverage Agent Harness")
    parser.add_argument("--goal", required=True, help="수행할 목표/질문")
    parser.add_argument("--model", default="gemini", choices=["gemini", "ollama", "deepseek"])
    _default_data = os.path.join(_COVERAGE_DIR, "data")
    parser.add_argument("--data-dir", default=_default_data, help="입력 문서 폴더 경로")
    parser.add_argument("--max-retries", type=int, default=2)
    parser.add_argument("--verify", action="store_true", help="Search Verifier 활성화")
    _default_logs = os.path.join(_COVERAGE_DIR, "logs")
    parser.add_argument("--log-dir", default=_default_logs, help="실행 로그 저장 폴더")

    parser.add_argument("--gemini-model", default="gemini-2.5-flash")
    parser.add_argument("--ollama-model", default="llama3")
    parser.add_argument("--deepseek-model", default="deepseek-chat")

    args = parser.parse_args()

    docs = load_documents(args.data_dir)
    llm = build_llm(args)
    print(f"[run] 모델: {args.model} | 문서: {len(docs)}개 | verify: {args.verify}")

    state = CoverageState(
        user_goal=args.goal,
        documents=docs,
        max_retries=args.max_retries,
    )

    state = run_harness(state, llm, run_verify=args.verify)

    print("\n" + "=" * 50)
    print("최종 결과:")
    print("=" * 50)
    if state.final_output:
        print(state.final_output)
    else:
        print("[출력 없음] audit 결정:", state.audit_result)
        print("\n[현재 초안]:")
        print(state.draft_summary)

    save_run_log(state, log_dir=args.log_dir)
    show_flow(state)


if __name__ == "__main__":
    main()
