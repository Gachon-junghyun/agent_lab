# FILE: experiments/coverage_agent/state.py
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

from core.agent.base_state import BaseState
from core.agent.document import Document


@dataclass
class CoverageState(BaseState):
    documents: List[Document] = field(default_factory=list)
    task_plan: Optional[Dict[str, Any]] = None
    checklist: Optional[List[Dict]] = None
    draft_summary: Optional[str] = None
    coverage_map: Optional[Dict] = None
    judge_result: Optional[Dict] = None
    verify_result: Optional[Dict] = None
    final_output: Optional[str] = None
    audit_result: Optional[Dict] = None

    def docs_as_text(self) -> str:
        """노드에 넘길 문서 텍스트 블록"""
        return "\n\n---\n\n".join(
            f"[{d.id}] {d.filename}\n{d.content}" for d in self.documents
        )
