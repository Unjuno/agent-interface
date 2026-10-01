from __future__ import annotations
import time
import tkinter as tk

CLEAR = "CLEAR_PROGRESS"
WATCH = "UNCERTAIN_TRANSIENT"
HARD = "HARD_INVALIDATION"
STATE_COLOR = {
    CLEAR: "#00ff00",
    WATCH: "#ffff00",
    HARD: "#ff0000",
}

WIDTH = 320
HEIGHT = 240
SENTINEL = (10, 10, 11, 11)
PROGRESS_RECT = (20, 100, 140, 110)
HARM_RECT = (20, 140, 140, 150)

class LiveFixture:
    def __init__(self, root: tk.Tk, initial_state: str, event_log: list[dict]):
        self.root = root
        self.state = initial_state
        self.event_log = event_log
        self.progress = 0
        self.harm = 0
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="#000000", highlightthickness=0, bd=0)
        self.canvas.pack()
        self._sentinel = self.canvas.create_rectangle(*SENTINEL, fill=STATE_COLOR[self.state], outline=STATE_COLOR[self.state], width=0)
        self._progress = self.canvas.create_rectangle(*PROGRESS_RECT, fill="#000000", outline="#000000", width=0)
        self._harm = self.canvas.create_rectangle(*HARM_RECT, fill="#000000", outline="#000000", width=0)
        root.bind_all("<KeyPress-F8>", self._on_press, add="+")
        root.bind_all("<KeyRelease-F8>", self._on_release, add="+")
        self._render_scores()

    def _now(self) -> int:
        return time.perf_counter_ns()

    def emit(self, event: str, **kwargs) -> None:
        row = {"event": event, "t_ns": self._now(), **kwargs}
        self.event_log.append(row)

    def set_state(self, new_state: str, nominal_offset_ns: int) -> None:
        if new_state not in STATE_COLOR:
            raise ValueError("bad state")
        self.state = new_state
        self.canvas.itemconfigure(self._sentinel, fill=STATE_COLOR[new_state], outline=STATE_COLOR[new_state])
        self.root.update_idletasks()
        self.emit("state_transition", state=new_state, nominal_offset_ns=nominal_offset_ns)

    def _render_scores(self) -> None:
        # Each accepted useful effect paints 10 px of green; each invalid-state effect paints 10 px of red.
        px = min(PROGRESS_RECT[2] - PROGRESS_RECT[0], self.progress * 10)
        hx = min(HARM_RECT[2] - HARM_RECT[0], self.harm * 10)
        self.canvas.coords(self._progress, PROGRESS_RECT[0], PROGRESS_RECT[1], PROGRESS_RECT[0] + px, PROGRESS_RECT[3])
        self.canvas.itemconfigure(self._progress, fill="#00ff00" if px else "#000000", outline="#00ff00" if px else "#000000")
        self.canvas.coords(self._harm, HARM_RECT[0], HARM_RECT[1], HARM_RECT[0] + hx, HARM_RECT[3])
        self.canvas.itemconfigure(self._harm, fill="#ff0000" if hx else "#000000", outline="#ff0000" if hx else "#000000")
        self.root.update_idletasks()

    def _on_press(self, _event) -> None:
        self.emit("f8_press", state=self.state)

    def _on_release(self, _event) -> None:
        # Preserve the application-observed release timestamp separately from effect application.
        self.emit("f8_release", state=self.state)
        before_progress = self.progress
        before_harm = self.harm
        if self.state == CLEAR:
            self.progress += 1
            kind = "useful"
        else:
            self.harm += 1
            kind = "harm"
        self._render_scores()
        self.emit(
            "f8_effect",
            state=self.state,
            effect_kind=kind,
            progress_before=before_progress,
            progress_after=self.progress,
            harm_before=before_harm,
            harm_after=self.harm,
        )
