# FILE: experiments/coverage_agent/nodes/extractor.py
"""
청크 기반 전수 추출 — Python이 분할을 보장하므로 누락 없음.

흐름:
  1. [Python] 문서 → 단락 단위 청크 분할 (전체 구간 확정)
  2. [LLM]    청크별 coverage item 추출
  3. [Python] 병합 + 중복 제거 + item_id 재부여
"""
import re
from typing import List, Dict

from core.ai.base import call_llm
from core.agent.utils import parse_json
from experiments.coverage_agent.state import CoverageState
from experiments.coverage_agent.prompts import EXTRACTOR_SYSTEM

_CHUNK_SIZE = 1500


def _split_into_chunks(text: str, max_chars: int = _CHUNK_SIZE) -> List[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: List[str] = []
    current = ""
    for para in paragraphs:
        if len(para) > max_chars:
            for sent in re.split(r"(?<=[.!?。])\s+", para):
                if len(current) + len(sent) + 1 > max_chars and current:
                    chunks.append(current.strip())
                    current = sent
                else:
                    current = (current + " " + sent).strip() if current else sent
        else:
            if len(current) + len(para) + 2 > max_chars and current:
                chunks.append(current.strip())
                current = para
            else:
                current = (current + "\n\n" + para).strip() if current else para
    if current:
        chunks.append(current.strip())
    return chunks


def _merge_items(all_items: List[Dict]) -> List[Dict]:
    """point 앞 10글자 기준으로 중복 제거 후 item_id 재부여."""
    seen: set = set()
    merged: List[Dict] = []
    for item in all_items:
        key = item.get("point", "")[:10].strip()
        if key and key not in seen:
            seen.add(key)
            merged.append(item)
    for i, item in enumerate(merged):
        item["item_id"] = f"c{i + 1}"
    return merged


def run_extractor(state: CoverageState, llm) -> CoverageState:
    doc_chunks = [
        {"source_id": doc.id, "chunk_idx": idx, "text": chunk}
        for doc in state.documents
        for idx, chunk in enumerate(_split_into_chunks(doc.content))
    ]
    total = len(doc_chunks)
    state.log(f"Extractor 시작 — {total}개 청크 전수 처리")

    all_items: List[Dict] = []
    guideline = getattr(state, "active_guideline", "")

    for i, chunk in enumerate(doc_chunks):
        label = f"[{chunk['source_id']} chunk {chunk['chunk_idx'] + 1}]"
        user = f"사용자 목표: {state.user_goal}\n\n문서 구간 {label}:\n{chunk['text']}"
        raw = call_llm(llm, EXTRACTOR_SYSTEM, user, guideline=guideline)
        items = parse_json(raw).get("coverage_items", [])
        all_items.extend(items)
        state.log(f"  청크 {i + 1}/{total} {label} → {len(items)}개 항목")

    merged = _merge_items(all_items)
    state.checklist = merged
    high = sum(1 for c in merged if c.get("priority") == "high")
    state.log(f"체크리스트 완성: {len(merged)}개 (high: {high}개, 원본 {len(all_items)}개에서 중복 제거)")
    state.trace("extractor", f"청크 {total}개 전수 처리",
                f"원본 {len(all_items)}개 → 병합 후 {len(merged)}개",
                {"coverage_items": merged})
    return state
