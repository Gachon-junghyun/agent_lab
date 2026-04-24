# FILE: core/ai/ollama_client.py
# @core-candidate: OllamaClient, 2026-04, Ollama 로컬 모델 연동 클라이언트

import logging
from typing import List, Dict, Any, Optional, Union, Generator

try:
    import ollama
except ImportError:
    ollama = None

log = logging.getLogger(__name__)


class OllamaClient:
    def __init__(self, model_name: str = "llama3", host: Optional[str] = "http://localhost:11434"):
        if ollama is None:
            raise ImportError("ollama 패키지가 없습니다. 'pip install ollama'를 실행하세요.")
        self.client = ollama.Client(host=host)
        self.model_name = model_name
        self.system_instruction: Optional[str] = None  # call_llm 통합 인터페이스 호환

    def generate(
        self,
        prompt: str,
        stream: bool = False,
        options: Optional[Dict[str, Any]] = None,
    ) -> Union[str, Generator[str, None, None]]:
        try:
            if stream:
                return self._generate_stream(prompt, options)
            response = self.client.generate(model=self.model_name, prompt=prompt, options=options)
            return response["response"]
        except Exception as e:
            log.error(f"Ollama Generate 오류: {e}")
            raise

    def _generate_stream(self, prompt: str, options: Optional[Dict]) -> Generator[str, None, None]:
        for chunk in self.client.generate(model=self.model_name, prompt=prompt, stream=True, options=options):
            yield chunk["response"]

    def chat(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        options: Optional[Dict[str, Any]] = None,
    ) -> Union[str, Generator[str, None, None]]:
        try:
            if stream:
                return self._chat_stream(messages, options)
            response = self.client.chat(model=self.model_name, messages=messages, options=options)
            return response["message"]["content"]
        except Exception as e:
            log.error(f"Ollama Chat 오류: {e}")
            raise

    def _chat_stream(self, messages: List[Dict[str, str]], options: Optional[Dict]) -> Generator[str, None, None]:
        for chunk in self.client.chat(model=self.model_name, messages=messages, stream=True, options=options):
            yield chunk["message"]["content"]

    def list_models(self) -> List[str]:
        models = self.client.list()
        return [m["name"] for m in models["models"]]
