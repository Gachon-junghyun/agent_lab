# FILE: core/ai/gemini_client.py
# @core-candidate: GeminiClient, 2026-04, Gemini API 연동 클라이언트

import os
import logging
from typing import List, Dict, Any, Optional, Union, Generator
from google import genai
from google.genai import types
from dotenv import load_dotenv

log = logging.getLogger(__name__)


class GeminiClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-2.5-flash",
        system_instruction: Optional[str] = None,
    ):
        load_dotenv()
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY 환경변수를 설정하거나 api_key를 전달하세요.")
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = model_name
        self.system_instruction = system_instruction

    def generate(
        self,
        prompt: str,
        stream: bool = False,
        config: Optional[Dict[str, Any]] = None,
    ) -> Union[str, Generator[str, None, None]]:
        gen_config = types.GenerateContentConfig(
            system_instruction=self.system_instruction,
            temperature=config.get("temperature", 0.1) if config else 0.1,
            max_output_tokens=config.get("max_output_tokens") if config else None,
        )
        try:
            if stream:
                return self._generate_stream(prompt, gen_config)
            response = self.client.models.generate_content(
                model=self.model_name, contents=prompt, config=gen_config
            )
            return response.text
        except Exception as e:
            log.error(f"Gemini API 오류: {e}")
            raise

    def _generate_stream(self, prompt: str, config: types.GenerateContentConfig) -> Generator[str, None, None]:
        for chunk in self.client.models.generate_content_stream(
            model=self.model_name, contents=prompt, config=config
        ):
            if chunk.text:
                yield chunk.text

    def chat(self, messages: List[Dict[str, str]], config: Optional[Dict[str, Any]] = None) -> str:
        contents = []
        for msg in messages:
            role = msg["role"] if msg["role"] in ("user", "model") else "user"
            contents.append(types.Content(
                role=role,
                parts=[types.Part.from_text(text=msg["content"])],
            ))
        gen_config = types.GenerateContentConfig(
            system_instruction=self.system_instruction,
            temperature=config.get("temperature", 0.1) if config else 0.1,
        )
        response = self.client.models.generate_content(
            model=self.model_name, contents=contents, config=gen_config
        )
        return response.text
