# core/ui — Agent Flow GUI 사용법

에이전트 실행 흐름을 **화살표 그래프 + 클릭 상세 패널**로 시각화하는 tkinter GUI 모듈.

---

## 설치 조건

별도 설치 없음. Python 기본 내장 `tkinter` 사용.

---

## 기본 사용법

```python
from core.ui import show_flow

# 에이전트 실행 후 (state.node_traces 가 쌓인 뒤)
show_flow(state)
```

> `show_flow`는 창을 닫을 때까지 **블로킹**된다.  
> 반드시 에이전트 실행이 끝난 후 마지막에 호출할 것.

---

## coverage_agent 연동 예시

```python
# experiments/coverage_agent/run.py

from core.ui import show_flow
from experiments.coverage_agent.harness import run_harness, save_run_log

state = run_harness(state, llm)
save_run_log(state)

show_flow(state)   # ← 이 줄 한 줄로 GUI 열림
```

---

## 직접 traces 목록으로 열기

`BaseState` 객체 없이 `node_traces` 리스트를 직접 넘길 수도 있다.

```python
from core.ui import show_flow

class _Fake:
    user_goal = "테스트 목표"
    node_traces = [
        {
            "node": "planner",
            "input_prompt": "사용자 목표: ...",
            "raw_response": "1단계: ...",
            "parsed": {"task_type": "summarization"},
            "timestamp": "2026-04-24T10:00:00",
        },
        {
            "node": "extractor",
            "input_prompt": "문서에서 핵심 발췌: ...",
            "raw_response": "핵심 내용: ...",
            "parsed": None,
            "timestamp": "2026-04-24T10:00:05",
        },
    ]

show_flow(_Fake())
```

---

## GUI 화면 구성

```
┌──────────────────────────────────────────────────────────────────┐
│  목표: [user_goal 텍스트]                                         │
├──────────────────────┬───────────────────────────────────────────┤
│  흐름도 (왼쪽)       │  상세 패널 (오른쪽)                       │
│                      │                                           │
│  ┌──────────────┐    │  ◆ planner                               │
│  │   planner    │    │     2026-04-24 10:00:00                   │
│  └──────┬───────┘    │                                           │
│         │  ↓         │  ── INPUT PROMPT ──                      │
│  ┌──────────────┐    │  사용자 목표: ...                         │
│  │  extractor   │    │                                           │
│  └──────┬───────┘    │  ── RAW RESPONSE ──                      │
│         │  ↓         │  1단계: ...                               │
│  ┌──────────────┐    │                                           │
│  │  summarizer  │    │  ── PARSED ──                            │
│  └──────────────┘    │  {"task_type": "summarization"}           │
│                      │                                           │
│  [노드 왼쪽: 응답 글자수]                                         │
│  [노드 오른쪽: 타임스탬프]                                        │
└──────────────────────┴───────────────────────────────────────────┘
│  선택됨: planner | 2026-04-24 10:00:00                           │
└──────────────────────────────────────────────────────────────────┘
```

- 노드 클릭 → 오른쪽에 INPUT PROMPT / RAW RESPONSE / PARSED 표시
- 마우스 휠 → 흐름도 스크롤 (노드가 많을 때)
- 노드 왼쪽 숫자: 응답 글자 수 (길이 가늠용)

---

## 전제 조건: state.trace() 호출

GUI는 `state.node_traces`를 읽는다.  
각 노드 함수 안에서 `state.trace()`를 호출해야 데이터가 쌓인다.

```python
# nodes/planner.py 예시
def run_planner(state, llm):
    prompt = build_prompt(state)
    response = llm.call(prompt)
    state.trace("planner", prompt, response, parsed_result)  # ← 필수
    return state
```

`state.trace()` 시그니처 (`core/agent/base_state.py`):
```python
def trace(self, node_name: str, input_prompt: str, raw_response: str, parsed: Any): ...
```

---

## 공개 API

| 함수 | 설명 |
|------|------|
| `show_flow(state, title="")` | GUI 실행. 창 닫을 때까지 블로킹 |

`title` 파라미터로 목표 텍스트를 직접 지정할 수 있다 (기본값: `state.user_goal`).
