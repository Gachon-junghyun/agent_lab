# FILE: core/orchestrator/harness.py
# @core-candidate: OrchestratorHarness, 2026-04, ToolRegistry 기반 ReAct 루프
from typing import Any, Callable, Dict, List, Optional, Tuple

from core.tool.registry import ToolRegistry
from core.orchestrator.guideline_store import GuidelineStore
from core.orchestrator.guideline_refiner import GuidelineRefiner
from core.orchestrator.main_llm import MainLLM


class OrchestratorHarness:
    """
    ToolRegistry에서 시맨틱 검색으로 툴을 찾아 실행하는 ReAct 루프.

    Args:
        registry:           등록된 툴을 보유한 ToolRegistry
        llm:                메인 오케스트레이터 LLM
        tool_llm:           각 AgentTool 내부에서 쓸 LLM (None이면 llm 재사용)
        refiner_llm:        가이드라인 개선 LLM (None이면 llm 재사용)
        initial_guidelines: {tool_name: 초기 가이드라인}
        judge_fn:           (tool_name, state) -> ("pass"|"fail", reason)
                            None이면 모든 결과 pass 처리
        search_top_k:       registry 검색 시 반환할 후보 수
        max_steps:          루프 최대 횟수
        max_retries:        툴당 최대 재시도 횟수
    """

    def __init__(
        self,
        registry: ToolRegistry,
        llm: Any,
        tool_llm: Any = None,
        refiner_llm: Any = None,
        initial_guidelines: Optional[Dict[str, str]] = None,
        judge_fn: Optional[Callable[[str, Any], Tuple[str, str]]] = None,
        search_top_k: int = 4,
        max_steps: int = 12,
        max_retries: int = 2,
    ) -> None:
        self._registry = registry
        self._main = MainLLM(llm)
        self._tool_llm = tool_llm or llm
        self._refiner = GuidelineRefiner(refiner_llm or llm)
        self._store = GuidelineStore(initial_guidelines or {})
        self._judge_fn = judge_fn
        self._top_k = search_top_k
        self._max_steps = max_steps
        self._max_retries = max_retries

    def run(self, state: Any) -> Any:
        """
        state를 받아 ReAct 루프를 실행하고 수정된 state를 반환.
        state는 BaseState 호환 객체 (user_goal, node_traces 등).
        """
        history: List[str] = []
        all_tools = self._registry.all_tools()

        print(f"\n{'='*54}")
        print(f"[Orchestrator] 목표: {state.user_goal}")
        print(f"[Orchestrator] 등록된 툴: {[t.name for t in all_tools]}")
        print(f"{'='*54}\n")

        for step in range(1, self._max_steps + 1):
            # 현재 상태에 맞는 툴 후보 검색
            query = self._build_search_query(state, history)
            candidates = self._registry.search(query, top_k=self._top_k)

            # Main LLM: 다음 액션 결정
            decision = self._main.decide(state, candidates, self._store, history)
            print(f"  [Step {step}] thought: {decision.thought}")

            if decision.done or decision.action is None:
                print(f"\n[Orchestrator] 완료 (총 {step}스텝)\n")
                return state

            tool = self._registry.get(decision.action)
            if tool is None:
                state.log(f"[Orchestrator] 알 수 없는 툴: {decision.action}")
                break

            # 툴 실행 (실패 시 가이드라인 업데이트 후 재시도)
            state = self._run_with_retry(tool, state, decision.action)
            history.append(f"[Step {step}] {decision.action} 실행 완료")

        print(f"\n[Orchestrator] max_steps({self._max_steps}) 도달\n")
        return state

    # ── 내부 ─────────────────────────────────────────────────────────────

    def _build_search_query(self, state: Any, history: List[str]) -> str:
        """현재 state에서 '다음에 필요한 작업'을 설명하는 쿼리 생성."""
        if not getattr(state, "task_plan", None):
            return "작업 계획 수립 목표 분석"
        if not getattr(state, "checklist", None):
            return "문서 내용 추출 체크리스트"
        if not getattr(state, "draft_summary", None):
            return "요약 생성 초안 작성"
        if not getattr(state, "judge_result", None):
            return "요약 품질 평가 검증"
        verdict = (state.judge_result or {}).get("verdict", "fail")
        if verdict == "fail" and getattr(state, "retry_count", 0) < getattr(state, "max_retries", 2):
            return "요약 재작성 수정 보완"
        if not getattr(state, "audit_result", None):
            return "최종 감사 릴리스 결정"
        return "완료"

    def _run_with_retry(self, tool: Any, state: Any, tool_name: str) -> Any:
        for attempt in range(self._max_retries + 1):
            guideline = self._store.get(tool_name)
            new_state = tool.run(state, self._tool_llm, guideline)

            if self._judge_fn is None:
                return new_state

            verdict, reason = self._judge_fn(tool_name, new_state)
            if verdict == "pass":
                return new_state

            print(f"  [Judge] {tool_name} FAIL (시도 {attempt + 1}) — {reason}")
            if attempt < self._max_retries:
                new_gl = self._refiner.refine(
                    tool_name, guideline,
                    tool_output=str(reason),
                    fail_reason=reason,
                )
                self._store.update(tool_name, new_gl)
                print(f"  [Refiner] {tool_name} 가이드라인 업데이트")
            state = new_state

        return state
