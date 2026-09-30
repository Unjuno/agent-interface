from __future__ import annotations

import argparse
import json
from pathlib import Path
import time
import tkinter as tk

from engine import BenchmarkSession, HEIGHT, HUD_HEIGHT, WIDTH, fresh_seed, generate_episode


SERIES = {
    "blue": "#4c78a8",
    "red": "#e45756",
    "green": "#54a24b",
    "yellow": "#eeca3b",
    "purple": "#b279a2",
    "orange": "#f58518",
}


class ArenaApp:
    def __init__(self, root: tk.Tk, session: BenchmarkSession, report_path: Path, clock_mode: str, autoclose: float | None):
        self.root = root
        self.session = session
        self.report_path = report_path
        self.clock_mode = clock_mode
        self.autoclose = autoclose
        self.last_wall = time.monotonic()
        self.finished_wall: float | None = None
        self.report_written = False

        root.title("Procedural Control Arena v0")
        root.resizable(False, False)
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="#111318", highlightthickness=0)
        self.canvas.pack()
        self.canvas.focus_set()
        self.canvas.bind("<Button-1>", self._click)
        self.canvas.bind("<KeyPress>", self._key_press)
        self.canvas.bind("<KeyRelease>", self._key_release)
        root.protocol("WM_DELETE_WINDOW", self._close)
        self._render()
        root.after(16, self._tick)

    def _key_press(self, event: tk.Event) -> None:
        if self.session.stage.kind == "typing" and self.session.terminal_focused:
            self.session.text_key(str(event.keysym), str(event.char))
        else:
            self.session.key_down(str(event.keysym))

    def _key_release(self, event: tk.Event) -> None:
        self.session.key_up(str(event.keysym))

    def _click(self, event: tk.Event) -> None:
        self.session.click(float(event.x), float(event.y))
        self.canvas.focus_set()

    def _tick(self) -> None:
        now = time.monotonic()
        if self.clock_mode == "realtime":
            dt = min(0.1, max(0.0, now - self.last_wall))
        else:
            dt = 1.0 / 60.0
        self.last_wall = now
        self.session.step(dt)
        self._render()
        if self.session.done:
            if not self.report_written:
                self._write_report()
                self.finished_wall = now
            if self.autoclose is not None and self.finished_wall is not None and now - self.finished_wall >= self.autoclose:
                self._close()
                return
        self.root.after(16, self._tick)

    def _draw_shape(self, obj) -> None:
        c = SERIES.get(obj.color, "#dddddd")
        r = obj.radius
        x, y = obj.x, obj.y
        if obj.shape == "circle":
            self.canvas.create_oval(x-r, y-r, x+r, y+r, fill=c, outline="#f2f2f2", width=2)
        elif obj.shape == "square":
            self.canvas.create_rectangle(x-r, y-r, x+r, y+r, fill=c, outline="#f2f2f2", width=2)
        elif obj.shape == "triangle":
            self.canvas.create_polygon(x, y-r, x-r, y+r, x+r, y+r, fill=c, outline="#f2f2f2", width=2)
        elif obj.shape == "diamond":
            self.canvas.create_polygon(x, y-r, x-r, y, x, y+r, x+r, y, fill=c, outline="#f2f2f2", width=2)

    def _render(self) -> None:
        self.canvas.delete("all")
        self.canvas.create_rectangle(0, 0, WIDTH, HUD_HEIGHT, fill="#1d2027", outline="")
        instruction = self.session.instruction()
        self.canvas.create_text(18, 18, anchor="nw", text=instruction, fill="#f2f2f2", font=("TkDefaultFont", 15, "bold"), width=WIDTH-36)
        if not self.session.done:
            remain = max(0.0, self.session.deadline() - self.session.stage_elapsed)
            status = f"stage {self.session.stage_index + 1}/{len(self.session.spec.stages)}  ·  time {remain:0.2f}s"
        else:
            status = f"episode {'PASS' if self.session.success else 'FAIL'}  ·  seed revealed in report"
        self.canvas.create_text(18, 72, anchor="nw", text=status, fill="#aeb6c2", font=("TkDefaultFont", 10))
        self.canvas.create_line(0, HUD_HEIGHT, WIDTH, HUD_HEIGHT, fill="#424854")

        if self.session.done:
            label = "PASS" if self.session.success else f"FAIL\n{self.session.failure_reason}"
            self.canvas.create_text(WIDTH/2, (HUD_HEIGHT+HEIGHT)/2, text=label, fill="#f2f2f2", font=("TkDefaultFont", 32, "bold"), justify="center")
            return

        stage = self.session.stage
        p = stage.payload
        if stage.kind == "move":
            x, y, r = p["zone_x"], p["zone_y"], p["zone_radius"]
            self.canvas.create_oval(x-r, y-r, x+r, y+r, outline="#d7dde8", width=4, dash=(8, 6))
            px, py = self.session.player_x, self.session.player_y
            self.canvas.create_polygon(px, py-12, px-10, py+10, px+10, py+10, fill="#f2f2f2", outline="")
        elif stage.kind in {"target", "switch"}:
            for obj in self.session.objects:
                self._draw_shape(obj)
            if stage.kind == "switch" and self.session.stage_elapsed < p["wait_seconds"]:
                fraction = max(0.0, min(1.0, self.session.stage_elapsed / p["wait_seconds"]))
                self.canvas.create_rectangle(20, HEIGHT-18, 20+(WIDTH-40)*fraction, HEIGHT-10, fill="#9aa4b2", outline="")
        elif stage.kind == "typing":
            tx, ty, tw, th = p["terminal_x"], p["terminal_y"], p["terminal_w"], p["terminal_h"]
            outline = "#f2f2f2" if self.session.terminal_focused else "#6f7886"
            self.canvas.create_rectangle(tx, ty, tx+tw, ty+th, fill="#202630", outline=outline, width=3)
            shown = self.session.text_buffer if self.session.terminal_focused else "click terminal"
            self.canvas.create_text(tx+10, ty+th/2, anchor="w", text=shown, fill="#f2f2f2", font=("TkFixedFont", 13, "bold"))

    def _write_report(self) -> None:
        self.report_path.parent.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(self.session.report(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        self.report_written = True
        print(f"report={self.report_path}")
        print(f"success={self.session.success}")
        print(f"fingerprint={self.session.spec.public_fingerprint()}")
        print(f"seed={self.session.spec.seed}")

    def _close(self) -> None:
        if not self.report_written:
            self._write_report()
        self.root.destroy()


def main() -> int:
    parser = argparse.ArgumentParser(description="Ultra-light procedural Agent Interface control benchmark")
    parser.add_argument("--seed", type=int, default=None, help="Replay seed. Omit for a fresh hidden seed.")
    parser.add_argument("--difficulty", type=float, default=0.35, help="Continuous difficulty in [0,1].")
    parser.add_argument("--clock", choices=("realtime", "fixed"), default="realtime")
    parser.add_argument("--report", default="arena-report.json")
    parser.add_argument("--autoclose", type=float, default=None, help="Close N seconds after completion.")
    args = parser.parse_args()

    seed = fresh_seed() if args.seed is None else args.seed
    spec = generate_episode(seed, args.difficulty)
    session = BenchmarkSession(spec)
    root = tk.Tk()
    ArenaApp(root, session, Path(args.report), args.clock, args.autoclose)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
