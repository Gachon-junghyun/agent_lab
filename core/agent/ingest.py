# FILE: core/agent/ingest.py
# @core-candidate: load_documents, 2026-04, .txt/.md/.pdf 문서 로더
from pathlib import Path
from typing import List

from core.agent.document import Document

try:
    import pdfplumber
    _PDF_OK = True
except ImportError:
    _PDF_OK = False

SUPPORTED_EXTS = {".txt", ".md", ".pdf"}


def _read_pdf(fp: Path) -> str:
    if not _PDF_OK:
        print(f"  [ingest] PDF 스킵 ({fp.name}) — pdfplumber 없음. 'pip install pdfplumber'")
        return ""
    pages = []
    with pdfplumber.open(fp) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text.strip())
    return "\n\n".join(pages)


def load_documents(data_dir: str = "data") -> List[Document]:
    """data/ 폴더의 .txt, .md, .pdf 파일을 모두 읽어 Document 리스트로 반환."""
    data_path = Path(data_dir)
    if not data_path.exists():
        print(f"[ingest] data 폴더 없음: {data_path.resolve()} — 빈 문서로 진행합니다.")
        return []

    docs: List[Document] = []
    for idx, fp in enumerate(sorted(data_path.iterdir())):
        if fp.suffix.lower() not in SUPPORTED_EXTS:
            continue
        try:
            content = _read_pdf(fp) if fp.suffix.lower() == ".pdf" else fp.read_text(encoding="utf-8").strip()
            if not content:
                continue
            docs.append(Document(id=f"doc{idx+1}", filename=fp.name, content=content))
            print(f"  [ingest] 로드: {fp.name} ({len(content):,}자)")
        except Exception as e:
            print(f"  [ingest] 오류 ({fp.name}): {e}")

    print(f"  [ingest] 총 {len(docs)}개 문서 로드 완료\n")
    return docs


def save_to_data(filename: str, content: str, data_dir: str = "data") -> str:
    """검색 결과 또는 외부 텍스트를 data/ 폴더에 저장"""
    data_path = Path(data_dir)
    data_path.mkdir(exist_ok=True)
    fp = data_path / filename
    fp.write_text(content, encoding="utf-8")
    print(f"  [ingest] 저장: {fp.resolve()}")
    return str(fp)
