# FILE: core/tool/embedding_tool.py
# @core-candidate: EmbeddingTool, 2026-04, 문서 청크 임베딩 + 유사도 검색
import math
import os
import re
from typing import List, Optional

from dotenv import load_dotenv

from core.tool.base_tool import BaseTool

_DEFAULT_CHUNK_SIZE = 500
_DEFAULT_CHUNK_OVERLAP = 80
_DEFAULT_TOP_K = 5

# google-genai SDK에서 지원하는 임베딩 모델 후보 (순서대로 시도)
_EMBED_MODEL_CANDIDATES = [
    "text-embedding-004",
    "models/text-embedding-004",
    "embedding-001",
    "models/embedding-001",
]


class EmbeddingTool(BaseTool):
    name = "embedding_retrieval"
    description = (
        "문서 청크에서 질의와 의미적으로 유사한 내용을 검색한다. "
        "input: 검색할 질의 문자열."
    )

    def __init__(self, documents, api_key: Optional[str] = None) -> None:
        load_dotenv()
        self._api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        self._chunks: List[str] = self._chunk(documents)
        self._embeddings: Optional[List[List[float]]] = None
        self._embed_model: Optional[str] = None
        self._use_keyword_fallback = False

        self._init_embeddings()

    # ── 초기화 ────────────────────────────────────────────────────────────

    def _init_embeddings(self) -> None:
        if not self._api_key:
            print("  [EmbeddingTool] API 키 없음 → 키워드 유사도 모드")
            self._use_keyword_fallback = True
            return

        try:
            from google import genai
            self._client = genai.Client(api_key=self._api_key)
            self._embed_model = self._find_working_model()
        except Exception as e:
            print(f"  [EmbeddingTool] 임베딩 API 초기화 실패: {e} → 키워드 유사도 모드")
            self._use_keyword_fallback = True
            return

        if self._embed_model is None:
            print("  [EmbeddingTool] 사용 가능한 임베딩 모델 없음 → 키워드 유사도 모드")
            self._use_keyword_fallback = True
            return

        print(f"  [EmbeddingTool] {len(self._chunks)}개 청크 임베딩 중 (모델: {self._embed_model})...")
        try:
            self._embeddings = [self._embed_api(c) for c in self._chunks]
            print(f"  [EmbeddingTool] 인덱싱 완료")
        except Exception as e:
            print(f"  [EmbeddingTool] 임베딩 실패: {e} → 키워드 유사도 모드")
            self._use_keyword_fallback = True

    def _find_working_model(self) -> Optional[str]:
        """후보 모델 중 실제로 동작하는 것을 반환."""
        test_text = "test"
        for model in _EMBED_MODEL_CANDIDATES:
            try:
                result = self._client.models.embed_content(model=model, contents=test_text)
                _ = result.embeddings[0].values
                return model
            except Exception:
                continue
        return None

    # ── 청킹 ──────────────────────────────────────────────────────────────

    @staticmethod
    def _chunk(documents) -> List[str]:
        chunks = []
        step = _DEFAULT_CHUNK_SIZE - _DEFAULT_CHUNK_OVERLAP
        for doc in documents:
            text = getattr(doc, "content", str(doc))
            for i in range(0, len(text), step):
                piece = text[i : i + _DEFAULT_CHUNK_SIZE].strip()
                if piece:
                    chunks.append(piece)
        return chunks

    # ── 유사도 계산 ───────────────────────────────────────────────────────

    def _embed_api(self, text: str) -> List[float]:
        result = self._client.models.embed_content(model=self._embed_model, contents=text)
        return result.embeddings[0].values

    @staticmethod
    def _cosine(a: List[float], b: List[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm = math.sqrt(sum(x**2 for x in a)) * math.sqrt(sum(x**2 for x in b))
        return dot / (norm + 1e-9)

    @staticmethod
    def _keyword_score(query: str, chunk: str) -> float:
        """폴백: Jaccard 유사도 기반 키워드 겹침 점수."""
        q = set(query.lower().split())
        c = set(chunk.lower().split())
        if not q or not c:
            return 0.0
        return len(q & c) / len(q | c)

    # ── 공개 인터페이스 ───────────────────────────────────────────────────

    def run(self, input: str, guideline: str = "") -> str:
        top_k = _DEFAULT_TOP_K
        m = re.search(r"top_k\s*=\s*(\d+)", guideline)
        if m:
            top_k = int(m.group(1))

        if self._use_keyword_fallback or self._embeddings is None:
            scored = sorted(
                enumerate(self._chunks),
                key=lambda x: self._keyword_score(input, x[1]),
                reverse=True,
            )
        else:
            query_emb = self._embed_api(input)
            scored = sorted(
                enumerate(self._embeddings),
                key=lambda x: self._cosine(query_emb, x[1]),
                reverse=True,
            )

        top_chunks = [self._chunks[i] for i, _ in scored[:top_k]]
        return "\n\n---\n\n".join(top_chunks)
