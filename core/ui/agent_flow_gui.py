# FILE: core/ui/agent_flow_gui.py
# @core-candidate: show_flow, 2026-04, BaseState node_traces GUI 시각화
import json
import tkinter as tk
from tkinter import messagebox
from typing import Any, Dict, List, Optional


_NODE_W = 180
_NODE_H = 44
_NODE_GAP = 64
_PAD = 40
_COLOR_DEFAULT = "#4A90D9"
_COLOR_SELECTED = "#1A5FA8"
_COLOR_ARROW = "#555555"


class _FlowGUI:
    def __init__(self, root: tk.Tk, traces: List[Dict[str, Any]], goal: str) -> None:
        self.root = root
        self.traces = traces
        self.goal = goal
        self._selected: Optional[int] = None
        self._rects: Dict[int, int] = {}  # idx → canvas rect id

        self.root.title("Agent Flow Viewer")
        self.root.geometry("980x640")
        self.root.configure(bg="#f0f2f5")

        self._build_header()
        self._build_panes()
        self._draw_flow()

    # ── 레이아웃 ──────────────────────────────────────────────────────────

    def _build_header(self) -> None:
        goal_short = self.goal if len(self.goal) <= 80 else self.goal[:77] + "..."
        tk.Label(
            self.root,
            text=f"목표: {goal_short}",
            font=("Arial", 11, "bold"),
            bg="#f0f2f5",
            anchor="w",
            pady=8,
        ).pack(fill="x", padx=14)

    def _build_panes(self) -> None:
        pane = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg="#f0f2f5", sashwidth=6)
        pane.pack(fill="both", expand=True, padx=10, pady=(0, 6))

        # 왼쪽: 흐름도 캔버스
        left = tk.Frame(pane, bd=1, relief="solid", bg="white")
        pane.add(left, width=300)

        self.canvas = tk.Canvas(left, bg="white", highlightthickness=0)
        vsb = tk.Scrollbar(left, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<MouseWheel>", lambda e: self.canvas.yview_scroll(-1 * (e.delta // 120), "units"))

        # 오른쪽: 상세 패널
        right = tk.Frame(pane, bd=1, relief="solid", bg="white")
        pane.add(right)

        self.detail = tk.Text(
            right, wrap="word", font=("Consolas", 10),
            state="disabled", padx=12, pady=10, bg="white",
            relief="flat",
        )
        dsb = tk.Scrollbar(right, orient="vertical", command=self.detail.yview)
        self.detail.configure(yscrollcommand=dsb.set)
        dsb.pack(side="right", fill="y")
        self.detail.pack(fill="both", expand=True)

        # 하단 상태바
        self.status_var = tk.StringVar(value="노드를 클릭하면 입출력을 확인할 수 있습니다.")
        tk.Label(
            self.root, textvariable=self.status_var,
            anchor="w", fg="#888", font=("Arial", 9), bg="#f0f2f5",
        ).pack(fill="x", padx=14, pady=(0, 6))

    # ── 흐름도 그리기 ──────────────────────────────────────────────────────

    def _draw_flow(self) -> None:
        cx = _PAD + _NODE_W // 2
        y = _PAD

        for i, trace in enumerate(self.traces):
            x0, x1 = cx - _NODE_W // 2, cx + _NODE_W // 2
            y0, y1 = y, y + _NODE_H
            tag = f"node_{i}"

            # 이전 노드에서 화살표
            if i > 0:
                prev_y1 = _PAD + (i - 1) * (_NODE_H + _NODE_GAP) + _NODE_H
                self.canvas.create_line(
                    cx, prev_y1, cx, y0,
                    arrow=tk.LAST, width=2,
                    fill=_COLOR_ARROW, arrowshape=(10, 13, 4),
                )

            # 노드 박스
            rect = self.canvas.create_rectangle(
                x0, y0, x1, y1,
                fill=_COLOR_DEFAULT, outline="#2C5F8A", width=2,
                tags=("node", tag),
            )
            self._rects[i] = rect

            # 노드 이름
            self.canvas.create_text(
                cx, (y0 + y1) // 2,
                text=trace["node"],
                fill="white", font=("Arial", 10, "bold"),
                tags=("node", tag),
            )

            # 타임스탬프 (오른쪽 바깥)
            ts = trace.get("timestamp", "")[:19].replace("T", " ")
            self.canvas.create_text(
                x1 + 6, (y0 + y1) // 2,
                text=ts, anchor="w",
                fill="#999", font=("Arial", 8),
            )

            # 응답 길이 표시 (왼쪽 바깥)
            resp_len = len(trace.get("raw_response", ""))
            self.canvas.create_text(
                x0 - 6, (y0 + y1) // 2,
                text=f"{resp_len}자", anchor="e",
                fill="#aaa", font=("Arial", 8),
            )

            # 이벤트 바인딩
            self.canvas.tag_bind(tag, "<Button-1>", lambda e, idx=i: self._on_click(idx))
            self.canvas.tag_bind(tag, "<Enter>", lambda e, r=rect: self.canvas.itemconfig(r, fill="#3070BB"))
            self.canvas.tag_bind(tag, "<Leave>", lambda e, idx=i: self._reset_color(idx))

            y += _NODE_H + _NODE_GAP

        total_h = y + _PAD
        self.canvas.configure(scrollregion=(0, 0, _PAD * 2 + _NODE_W + 200, total_h))

    def _reset_color(self, idx: int) -> None:
        color = _COLOR_SELECTED if self._selected == idx else _COLOR_DEFAULT
        self.canvas.itemconfig(self._rects[idx], fill=color)

    # ── 클릭 핸들러 ───────────────────────────────────────────────────────

    def _on_click(self, idx: int) -> None:
        if self._selected is not None:
            self.canvas.itemconfig(self._rects[self._selected], fill=_COLOR_DEFAULT)
        self._selected = idx
        self.canvas.itemconfig(self._rects[idx], fill=_COLOR_SELECTED)
        self._render_detail(self.traces[idx])
        ts = self.traces[idx].get("timestamp", "")[:19]
        self.status_var.set(f"선택됨: {self.traces[idx]['node']}  |  {ts}")

    def _render_detail(self, trace: Dict[str, Any]) -> None:
        t = self.detail
        t.configure(state="normal")
        t.delete("1.0", "end")

        t.tag_config("h1", font=("Arial", 13, "bold"), foreground="#1a1a2e", spacing1=2)
        t.tag_config("meta", font=("Arial", 9), foreground="#888")
        t.tag_config("sec", font=("Consolas", 10, "bold"), foreground="#4A90D9", spacing1=10)
        t.tag_config("body", font=("Consolas", 10), foreground="#333")

        t.insert("end", f"◆  {trace['node']}\n", "h1")
        t.insert("end", f"   {trace.get('timestamp', '')[:19].replace('T', ' ')}\n\n", "meta")

        t.insert("end", "── INPUT PROMPT ──\n", "sec")
        t.insert("end", (trace.get("input_prompt") or "(없음)") + "\n", "body")

        t.insert("end", "── RAW RESPONSE ──\n", "sec")
        t.insert("end", (trace.get("raw_response") or "(없음)") + "\n", "body")

        parsed = trace.get("parsed")
        if parsed is not None:
            t.insert("end", "── PARSED ──\n", "sec")
            try:
                parsed_str = json.dumps(parsed, ensure_ascii=False, indent=2)
            except Exception:
                parsed_str = str(parsed)
            t.insert("end", parsed_str + "\n", "body")

        t.configure(state="disabled")
        t.see("1.0")


# ── 공개 API ──────────────────────────────────────────────────────────────

def show_flow(state: Any, title: str = "") -> None:
    """
    BaseState 실행 결과를 tkinter GUI로 시각화한다.

    Args:
        state: node_traces / user_goal 속성을 가진 객체 (BaseState 호환)
        title: 윈도우 상단 목표 텍스트 (생략 시 state.user_goal 사용)

    Note:
        블로킹 호출. 창을 닫을 때까지 반환되지 않는다.
        에이전트 실행이 모두 끝난 뒤 호출할 것.
    """
    traces: List[Dict[str, Any]] = getattr(state, "node_traces", [])
    goal: str = title or getattr(state, "user_goal", "")

    root = tk.Tk()

    if not traces:
        messagebox.showinfo("Agent Flow Viewer", "기록된 node_trace가 없습니다.\nstate.trace()를 호출했는지 확인하세요.")
        root.destroy()
        return

    _FlowGUI(root, traces, goal)
    root.mainloop()
