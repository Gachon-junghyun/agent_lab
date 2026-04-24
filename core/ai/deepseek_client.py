# FILE: core/ai/deepseek_client.py
# @core-candidate: DeepSeekClient, 2026-04, DeepSeek API 연동 클라이언트 (OpenAI-compatible)

import os
import logging
from typing import List, Dict, Optional
from openai import OpenAI
from dotenv import load_dotenv

log = logging.getLogger(__name__)


class DeepSeekClient:
    """
    DeepSeek API 클라이언트 (OpenAI-compatible).
    모델: deepseek-chat (V3), deepseek-reasoner (R1)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "deepseek-chat",
        system_instruction: Optional[str] = None,
    ):
        load_dotenv()
        api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY 환경변수를 설정하거나 api_key를 전달하세요.")
        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        self.model_name = model_name
        self.system_instruction = system_instruction

    def generate(self, prompt: str) -> str:
        messages: List[Dict[str, str]] = []
        if self.system_instruction:
            messages.append({"role": "system", "content": self.system_instruction})
        messages.append({"role": "user", "content": prompt})
        return self._complete(messages)

    def chat(self, messages: List[Dict[str, str]]) -> str:
        return self._complete(messages)

    def _complete(self, messages: List[Dict[str, str]]) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
            )
            return response.choices[0].message.content
        except Exception as e:
            log.error(f"DeepSeek API 오류: {e}")
            raise
