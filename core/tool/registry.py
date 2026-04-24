# FILE: core/tool/registry.py
# @core-candidate: ToolRegistry, 2026-04, 툴 등록 + 임베딩 기반 시맨틱 검색
import math
import os
import re
from typing import List, Optional

from dotenv import load_dotenv

from core.tool.base_tool import BaseTool

_EMBED_MODEL_CANDIDATES = [
    "text-embedding-004",
    "models/text-embedding-004",
    "embedding-001",
    "models/embedding-001",
]


class ToolRegistry:
    """
    툴을 등록하고 쿼리와 의미적으로 유사한 툴을 반환한다.
    Gemini 임베딩 API 사용 가능 시 코사인 유사도, 불가 시 키워드 Jaccard 폴백.
    """

    def __init__(self, api_key: Optional[str] = None) -> None:
        load_dotenv()
        self._tools: List[BaseTool] = []
        self._embeddings: List[List[float]] = []
        self._client = None
        self._embed_model: Optional[str] = None
        self._use_keyword = False
        self._init_embed_client(api_key)

    # ── 초기화 ────────────────────────────────────────────────────────────

    def _init_embed_client(self, api_key: Optional[str]) -> None:
        key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not key:
            print("  [Registry] API 키 없음 → 키워드 검색 모드")
            self._use_keyword = True
            return
        try:
            from google import genai
            self._client = genai.Client(api_key=key)
            self._embed_model = self._find_model()
        except Exception as e:
            print(f"  [Registry] 임베딩 클라이언트 초기화 실패: {e} → 키워드 모드")
            self._use_keyword = True
            return
        if not self._embed_model:
            print("  [Registry] 사용 가능한 임베딩 모델 없음 → 키워드 모드")
            self._use_keyword = True

    def _find_model(self) -> Optional[str]:
        for m in _EMBED_MODEL_CANDIDATES:
            try:
                r = self._client.models.embed_content(model=m, contents="test")
                _ = r.embeddings[0].values
                return m
            except Exception:
                continue
        return None

    # ── 등록 ──────────────────────────────────────────────────────────────

    def register(self, tool: BaseTool) -> None:
        self._tools.append(tool)
        if not self._use_keyword:
            try:
                self._embeddings.append(self._embed_api(tool.description))
            except Exception:
                self._use_keyword = True
                self._embeddings = []

    def register_all(self, tools: List[BaseTool]) -> None:
        for t in tools:
            self.register(t)

    # ── 검색 ──────────────────────────────────────────────────────────────

    def search(self, query: str, top_k: int = 3) -> List[BaseTool]:
        """쿼리와 가장 유사한 top_k개 툴을 반환."""
        if not self._tools:
            return []
        top_k = min(top_k, len(self._tools))

        if self._use_keyword or not self._embeddings:
            scores = [self._keyword_score(query, t.description) for t in self._tools]
        else:
            try:
                q_emb = self._embed_api(query)
                scores = [self._cosine(q_emb, e) for e in self._embeddings]
            except Exception:
                scores = [self._keyword_score(query, t.description) for t in self._tools]

        ranked = sorted(zip(scores, self._tools), key=lambda x: x[0], reverse=True)
        return [t for _, t in ranked[:top_k]]

    def get(self, name: str) -> Optional[BaseTool]:
        for t in self._tools:
            if t.name == name:
                return t
        return None

    def all_tools(self) -> List[BaseTool]:
        return list(self._tools)

    # ── 유사도 계산 ───────────────────────────────────────────────────────

    def _embed_api(self, text: str) -> List[float]:
        r = self._client.models.embed_content(model=self._embed_model, contents=text)
        return r.embeddings[0].values

    @staticmethod
    def _cosine(a: List[float], b: List[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm = math.sqrt(sum(x**2 for x in a)) * math.sqrt(sum(x**2 for x in b))
        return dot / (norm + 1e-9)

    @staticmethod
    def _keyword_score(query: str, text: str) -> float:
        q = set(re.findall(r'\w+', query.lower()))
        t = set(re.findall(r'\w+', text.lower()))
        if not q or not t:
            return 0.0
        return len(q & t) / len(q | t)
