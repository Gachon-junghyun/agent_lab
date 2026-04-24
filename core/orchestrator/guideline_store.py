# FILE: core/orchestrator/guideline_store.py
# @core-candidate: GuidelineStore, 2026-04, 툴별 가이드라인 상태 관리
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class GuidelineEntry:
    current: str
    history: List[str] = field(default_factory=list)
    fail_count: int = 0


class GuidelineStore:
    def __init__(self, initial: Dict[str, str]) -> None:
        self._store: Dict[str, GuidelineEntry] = {
            name: GuidelineEntry(current=gl) for name, gl in initial.items()
        }

    def get(self, tool_name: str) -> str:
        entry = self._store.get(tool_name)
        return entry.current if entry else ""

    def update(self, tool_name: str, new_guideline: str) -> None:
        if tool_name not in self._store:
            self._store[tool_name] = GuidelineEntry(current=new_guideline)
            return
        entry = self._store[tool_name]
        entry.history.append(entry.current)
        entry.current = new_guideline
        entry.fail_count += 1

    def snapshot(self) -> Dict[str, dict]:
        return {
            name: {
                "current": e.current,
                "fail_count": e.fail_count,
                "history": e.history,
            }
            for name, e in self._store.items()
        }
