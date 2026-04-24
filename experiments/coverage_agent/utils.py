# FILE: experiments/coverage_agent/utils.py
import json
import re
from typing import Dict, Tuple


def parse_coverage_response(text: str) -> Tuple[str, Dict]:
    """
    Summarizer 응답에서 summary 본문과 <coverage_map_json> 블록 분리.
    반환: (summary_text, coverage_map_dict)
    """
    tag_pattern = re.search(
        r"<coverage_map_json>\s*(\{.*?\})\s*</coverage_map_json>",
        text,
        re.DOTALL,
    )
    if tag_pattern:
        coverage_map = json.loads(tag_pattern.group(1))
        summary = text[: tag_pattern.start()].strip()
    else:
        coverage_map = {"included_items": [], "omitted_items": [], "note": "coverage_map 없음"}
        summary = text.strip()
    return summary, coverage_map
