# FILE: core/orchestrator/guideline_refiner.py
# @core-candidate: GuidelineRefiner, 2026-04, fail 이유 기반 가이드라인 자동 개선
from typing import Any

from core.ai.base import call_llm

_SYSTEM = """너는 AI 에이전트의 가이드라인을 개선하는 전문가다.
툴 이름, 현재 가이드라인, 실행 결과, 실패 이유를 받아 개선된 가이드라인을 한 문단으로 반환한다.
가이드라인은 해당 툴이 run()을 실행할 때 system instruction으로 주입된다.
반드시 구체적이고 실행 가능한 지시로 작성해라. 설명 없이 가이드라인 텍스트만 출력해라."""

_USER_TEMPLATE = """툴: {tool_name}

현재 가이드라인:
{current_guideline}

툴 실행 결과:
{tool_output}

실패 이유:
{fail_reason}

개선된 가이드라인을 작성해라."""


class GuidelineRefiner:
    def __init__(self, llm: Any) -> None:
        self._llm = llm

    def refine(
        self,
        tool_name: str,
        current_guideline: str,
        tool_output: str,
        fail_reason: str,
    ) -> str:
        user = _USER_TEMPLATE.format(
            tool_name=tool_name,
            current_guideline=current_guideline or "(없음)",
            tool_output=tool_output[:800],
            fail_reason=fail_reason,
        )
        return call_llm(self._llm, system=_SYSTEM, user=user).strip()
