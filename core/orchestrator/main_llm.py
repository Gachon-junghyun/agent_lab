# FILE: core/orchestrator/main_llm.py
# @core-candidate: MainLLM, 2026-04, state 요약 + 후보 툴 기반 다음 액션 결정
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from core.ai.base import call_llm
from core.agent.utils import parse_json

_SYSTEM = """너는 에이전트 오케스트레이터다. 현재 상태와 사용 가능한 툴 목록을 보고 다음에 실행할 툴을 결정한다.

아래 JSON만 출력한다:
{
  "thought": "현재 상태를 보고 다음에 뭘 해야 할지 한 줄 판단",
  "action": "실행할 툴 이름 (완료면 null)",
  "next_query": "action 실행 후 다음 스텝에서 필요한 작업을 10단어 이내로 설명 (done=true면 빈 문자열)",
  "done": true 또는 false
}

규칙:
- action은 반드시 제공된 툴 목록의 name 중 하나여야 한다.
- done=true는 final_output 또는 audit 결정이 완료됐을 때만 사용한다.
- next_query는 다음 스텝 툴 검색에 쓰이므로 구체적으로 작성한다.
- 마크다운 없이 JSON만 출력한다."""

_USER_TEMPLATE = """현재 상태:
{state_summary}

실행 이력:
{history}

사용 가능한 툴:
{tool_specs}

다음 액션을 결정해라."""


@dataclass
class ActionDecision:
    thought: str
    action: Optional[str]
    done: bool
    next_query: str = ""


class MainLLM:
    def __init__(self, llm: Any) -> None:
        self._llm = llm

    def decide(
        self,
        state: Any,
        candidate_tools: List[Any],
        guideline_store: Any,
        history: List[str],
    ) -> ActionDecision:
        tool_specs = "\n".join(
            f"- {t.name}: {t.description}"
            f"\n  [가이드라인: {guideline_store.get(t.name) or '기본'}]"
            for t in candidate_tools
        )
        user = _USER_TEMPLATE.format(
            state_summary=self._summarize_state(state),
            history="\n".join(history) or "(없음)",
            tool_specs=tool_specs,
        )
        raw = call_llm(self._llm, system=_SYSTEM, user=user)
        return self._parse(raw)

    @staticmethod
    def _summarize_state(state: Any) -> str:
        lines = [f"목표: {getattr(state, 'user_goal', '?')}"]
        checks = [
            ("task_plan",     lambda v: f"task_plan 수립됨 ({v.get('task_type', '?')})"),
            ("checklist",     lambda v: f"checklist {len(v)}개 항목 추출됨"),
            ("draft_summary", lambda v: f"draft_summary 작성됨 ({len(v)}자)"),
            ("coverage_map",  lambda v: f"coverage_map 생성됨"),
            ("judge_result",  lambda v: f"judge 결과: {v.get('verdict', '?')} (score={v.get('coverage_score', 0):.2f})"),
            ("verify_result", lambda v: f"verify_result 있음"),
            ("audit_result",  lambda v: f"audit 결정: {v.get('release_decision', '?')}"),
            ("final_output",  lambda v: f"final_output 완성됨 ({len(v)}자)"),
        ]
        for attr, fmt in checks:
            val = getattr(state, attr, None)
            if val:
                lines.append(f"  ✓ {fmt(val)}")
            else:
                lines.append(f"  ✗ {attr} 없음")
        retry = getattr(state, "retry_count", 0)
        if retry:
            lines.append(f"  재시도 횟수: {retry}")
        return "\n".join(lines)

    @staticmethod
    def _parse(raw: str) -> ActionDecision:
        try:
            data = parse_json(raw)
            return ActionDecision(
                thought=data.get("thought", ""),
                action=data.get("action"),
                done=bool(data.get("done", False)),
                next_query=data.get("next_query", ""),
            )
        except Exception:
            return ActionDecision(thought="파싱 실패", action=None, done=True)
