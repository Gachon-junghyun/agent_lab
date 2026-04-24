# FILE: core/ai/__init__.py
from typing import Any
from core.ai.gemini_client import GeminiClient
from core.ai.ollama_client import OllamaClient
from core.ai.deepseek_client import DeepSeekClient


def get_llm(name: str, **kwargs) -> Any:
    """
    LLM 클라이언트 팩토리.
    name: "gemini" | "ollama" | "deepseek"
    kwargs: 각 클라이언트 생성자 파라미터 (model_name, api_key 등)
    """
    name = name.lower()
    if name == "gemini":
        return GeminiClient(**kwargs)
    if name == "ollama":
        return OllamaClient(**kwargs)
    if name == "deepseek":
        return DeepSeekClient(**kwargs)
    raise ValueError(f"알 수 없는 LLM: {name!r}. 사용 가능: gemini, ollama, deepseek")
