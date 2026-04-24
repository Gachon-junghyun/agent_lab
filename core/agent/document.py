# FILE: core/agent/document.py
# @core-candidate: Document, 2026-04, 에이전트 공통 문서 단위
from dataclasses import dataclass


@dataclass
class Document:
    id: str
    filename: str
    content: str
