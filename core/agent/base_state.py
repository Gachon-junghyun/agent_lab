# FILE: core/agent/base_state.py
# @core-candidate: BaseState, 2026-04, 모든 에이전트 공통 상태 기반 클래스
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, List


@dataclass
class BaseState:
    user_goal: str
    status: str = "running"       # running | done | failed
    retry_count: int = 0
    max_retries: int = 2
    logs: List[str] = field(default_factory=list)
    node_traces: List[dict] = field(default_factory=list)
    active_guideline: str = ""    # 현재 실행 중인 툴의 가이드라인 (AgentTool이 주입)

    def log(self, msg: str):
        self.logs.append(msg)
        print(f"  → {msg}")

    def trace(self, node_name: str, input_prompt: str, raw_response: str, parsed: Any):
        """LLM 호출 1회의 입력/출력 전체를 기록. 콘솔에는 요약만 출력."""
        self.node_traces.append({
            "node": node_name,
            "input_prompt": input_prompt,
            "raw_response": raw_response,
            "parsed": parsed,
            "timestamp": datetime.now().isoformat(),
        })
        print(f"  [TRACE] {node_name} → {len(raw_response)}자 응답")
