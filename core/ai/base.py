# FILE: core/ai/base.py
# @core-candidate: call_llm, 2026-04, 세 클라이언트 공통 호출 인터페이스


def call_llm(llm, system: str, user: str) -> str:
    """
    GeminiClient / OllamaClient / DeepSeekClient를 동일 인터페이스로 호출.
    - Gemini: system_instruction per-call 세팅 후 generate()
    - Ollama / DeepSeek: chat([system, user])
    """
    if type(llm).__name__ == "GeminiClient":
        llm.system_instruction = system
        return llm.generate(user)
    return llm.chat([
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ])
