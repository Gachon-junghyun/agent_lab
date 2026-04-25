# FILE: core/ai/base.py
# @core-candidate: call_llm, 2026-04, 세 클라이언트 공통 호출 인터페이스


def call_llm(llm, system: str, user: str, guideline: str = "") -> str:
    """
    GeminiClient / OllamaClient / DeepSeekClient를 동일 인터페이스로 호출.
    guideline이 있으면 system prompt 끝에 자동 추가.
    """
    if guideline:
        system = f"{system}\n\n[가이드라인]\n{guideline}"
    if type(llm).__name__ == "GeminiClient":
        llm.system_instruction = system
        return llm.generate(user)
    return llm.chat([
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ])
