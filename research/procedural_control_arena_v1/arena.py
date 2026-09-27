from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
import tkinter as tk

from engine import (
    BenchmarkSession,
    DifficultyProfile,
    HEIGHT,
    PLAY_BOTTOM,
    PLAY_TOP,
    TICK_HZ,
    WIDTH,
    fresh_seed,
    generate_episode,
)

PALETTE = {
    "blue": "#3b82f6",
    "red": "#ef4444",
    "green": "#22c55e",
    "yellow": "#eab308",
    "purple": "#a855f7",
    "orange": "#f97316",
}


def _parse_overrides(items: list[str]) -> dict[str, float | int]:
    result: dict[str, float | int] = {}
    for item in items:
        if "=" not in item:
            raise argparse.ArgumentTypeError(f"expected KEY=VALUE, got {item!r}")
        key, value = item.split("=", 1)
        key = key.strip()
        value = value.strip()
        try:
            result[key] = float(value)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(f"invalid numeric value for {key}: {value}") from exc
    return result


class ArenaApp:
    def __init__(self, root: tk.Tk, session: BenchmarkSession, report_path: Path, clock_mode: str, autoclose: float | None):
        self.root = root
        self.session = session
        self.report_path = report_path
        self.clock_mode = clock_mode
        self.autoclose = autoclose
        self.report_written = False
        self.finished_wall: float | None = None
        self.last_tick = time.monotonic()
        self.mouse_down = False

        root.title("Procedural Control Arena v1")
        root.resizable(False, False)
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="#10151c", highlightthickness=0)
        self.canvas.pack()
        self.canvas.focus_set()

        root.bind("<KeyPress>", self._key_down)
        root.bind("<KeyRelease>", self._key_up)
        self.canvas.bind("<ButtonPress-1>", self._pointer_down)
        self.canvas.bind("<B1-Motion>", self._pointer_move)
        self.canvas.bind("<ButtonRelease-1>", self._pointer_up)
        root.protocol("WM_DELETE_WINDOW", self._close)
        root.after(16, self._tick)

    def _key_down(self, event: tk.Event) -> None:
        if self.session.done:
            return
        if self.session.stage.kind == "typing":
            self.session.text_key(event.keysym, event.char)
        else:
            key = event.keysym.lower()
            if key == "shift_l" or key == "shift_r":
                key = "shift"
            self.session.key_down(key)

    def _key_up(self, event: tk.Event) -> None:
        key = event.keysym.lower()
        if key in {"shift_l", "shift_r"}:
            key = "shift"
        self.session.key_up(key)

    def _pointer_down(self, event: tk.Event) -> None:
        self.mouse_down = True
        self.session.pointer_down(float(event.x), float(event.y))
        self.canvas.focus_set()

    def _pointer_move(self, event: tk.Event) -> None:
        if self.mouse_down:
            self.session.pointer_move(float(event.x), float(event.y))

    def _pointer_up(self, event: tk.Event) -> None:
        self.mouse_down = False
        self.session.pointer_up(float(event.x), float(event.y))

    def _tick(self) -> None:
        now = time.monotonic()
        dt = 1.0 / TICK_HZ if self.clock_mode == "fixed" else min(0.1, now - self.last_tick)
        self.last_tick = now
        if not self.session.done:
            self.session.step(dt)
        elif self.finished_wall is None:
            self.finished_wall = now
            self._write_report()
        self._render()
        if self.session.done and self.autoclose is not None and self.finished_wall is not None and now - self.finished_wall >= self.autoclose:
            self._close()
            return
        self.root.after(16, self._tick)

    def _shape(self, x: float, y: float, radius: float, shape: str, *, fill: str, outline: str, width: int = 2, dash=None) -> None:
        c = self.canvas
        kwargs = {"fill": fill, "outline": outline, "width": width}
        if dash is not None:
            kwargs["dash"] = dash
        if shape == "circle":
            c.create_oval(x-radius, y-radius, x+radius, y+radius, **kwargs)
        elif shape == "square":
            c.create_rectangle(x-radius, y-radius, x+radius, y+radius, **kwargs)
        elif shape == "diamond":
            c.create_polygon(x, y-radius, x-radius, y, x, y+radius, x+radius, y, **kwargs)
        else:
            c.create_polygon(x, y-radius, x-radius, y+radius, x+radius, y+radius, **kwargs)

    def _draw_objects(self) -> None:
        for obj in self.session.objects:
            if obj.locked:
                fill = PALETTE[obj.color]
                outline = "#d1fae5"
            else:
                fill = PALETTE[obj.color]
                outline = "#f8fafc"
            self._shape(obj.x, obj.y, obj.radius, obj.shape, fill=fill, outline=outline, width=2)

    def _draw_objective_sample(self, obj, *, border: str = "#22c55e", key: str | None = None) -> None:
        """Render desired state/constraint without naming the mechanic or prescribing a motor sequence."""
        c = self.canvas
        r = self.session.spec.difficulty.objective_sample_radius
        if key is None:
            c.create_rectangle(18, 15, 116, 92, fill="#17202b", outline=border, width=3)
            self._shape(67, 54, r, obj.shape, fill=PALETTE[obj.color], outline="#f8fafc", width=2)
            return
        c.create_rectangle(18, 15, 220, 92, fill="#17202b", outline=border, width=3)
        c.create_rectangle(31, 32, 103, 75, fill="#273548", outline="#cbd5e1", width=2)
        c.create_text(67, 54, text=key.upper(), fill="#f8fafc", font=("TkFixedFont", 11, "bold"))
        c.create_text(124, 54, text="+", fill="#94a3b8", font=("TkDefaultFont", 18, "bold"))
        self._shape(174, 54, r, obj.shape, fill=PALETTE[obj.color], outline="#f8fafc", width=2)

    def _render(self) -> None:
        c = self.canvas
        c.delete("all")
        c.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#10151c", outline="")
        c.create_line(0, PLAY_TOP-2, WIDTH, PLAY_TOP-2, fill="#475569", width=2)

        # Scorer result, failure reason, seed/fingerprint and hidden stage identity remain evaluator-only.
        if self.session.done:
            c.create_rectangle(165, 205, WIDTH-165, 305, fill="#17202b", outline="#64748b", width=2)
            c.create_text(WIDTH/2, 255, text="SESSION COMPLETE", fill="#cbd5e1",
                          font=("TkDefaultFont", 20, "bold"))
            return

        d = self.session.spec.difficulty
        kind, p = self.session.stage.kind, self.session.stage.payload

        if kind == "move":
            x, y, r = p["zone_x"], p["zone_y"], p["zone_radius"]
            c.create_oval(x-r, y-r, x+r, y+r, outline="#e2e8f0", width=3, dash=(8,4))
            px, py = self.session.player_x, self.session.player_y
            c.create_polygon(px, py-11, px-9, py+10, px+9, py+10, fill="#f8fafc", outline="#0f172a")
            return

        if kind in {"target", "combo", "recovery"}:
            target = self.session._object_by_id(p["target_id"])
            self._draw_objective_sample(
                target,
                border="#22c55e",
                key=str(p["required_key"]) if kind == "combo" else None,
            )
            self._draw_objects()
            return

        if kind == "switch":
            pending = self.session.stage_elapsed < float(p["wait_seconds"])
            target_id = p["prepared_id"] if pending else p["active_id"]
            target = self.session._object_by_id(target_id)
            self._draw_objective_sample(target, border="#f59e0b" if pending else "#22c55e")
            # A status lamp exposes readiness as world state without imperative WAIT/SWITCH prose.
            c.create_oval(WIDTH-58, 31, WIDTH-28, 61,
                          fill="#f59e0b" if pending else "#22c55e", outline="#f8fafc", width=2)
            self._draw_objects()
            return

        if kind == "typing":
            # The code itself is task data; the physical input recipe is intentionally not stated.
            code = str(p["code"])
            card_w = max(180, 22 * len(code))
            left = (WIDTH-card_w)/2
            c.create_rectangle(left, 18, left+card_w, 86, fill="#17202b", outline="#94a3b8", width=2)
            c.create_text(WIDTH/2, 52, text=code, fill="#f8fafc", font=("TkFixedFont", 18, "bold"))
            tx, ty, tw, th = p["terminal_x"], p["terminal_y"], p["terminal_w"], p["terminal_h"]
            outline = "#22c55e" if self.session.terminal_focused else "#94a3b8"
            c.create_rectangle(tx, ty, tx+tw, ty+th, fill="#202630", outline=outline, width=3)
            shown = self.session.text_buffer + ("|" if self.session.terminal_focused else "")
            c.create_text(tx+10, ty+th/2, anchor="w", text=shown, fill="#f2f2f2",
                          font=("TkFixedFont", 13, "bold"))
            return

        if kind == "drag":
            slot_x, slot_y, tol = p["slot_x"], p["slot_y"], p["tolerance"]
            piece = self.session.objects[0]
            self._shape(slot_x, slot_y, max(tol, piece.radius), piece.shape,
                        fill="", outline=PALETTE[piece.color], width=3, dash=(6,4))
            self._draw_objects()
            return

        if kind == "assembly":
            for slot in p["slots"]:
                self._shape(slot["x"], slot["y"], slot["radius"], slot["shape"],
                            fill="", outline=PALETTE[slot["color"]], width=2, dash=(5,4))
            self._draw_objects()
            c.create_line(WIDTH*0.5, PLAY_TOP+12, WIDTH*0.5, PLAY_BOTTOM-12, fill="#334155", width=2)
            return

        if kind == "trace":
            pts = p["points"]
            flat = [v for point in pts for v in point]
            c.create_line(*flat, fill="#64748b", width=max(2, int(p["tolerance"]*0.65)), smooth=True)
            for idx, (x,y) in enumerate(pts):
                r = max(5, p["tolerance"]*0.42)
                if idx == 0:
                    fill, outline = "#22c55e", "#dcfce7"
                elif idx <= self.session.trace_checkpoint and self.session.trace_started:
                    fill, outline = "#22c55e", "#cbd5e1"
                else:
                    fill, outline = "#1e293b", "#cbd5e1"
                c.create_oval(x-r, y-r, x+r, y+r, fill=fill, outline=outline, width=2)
            ex, ey = pts[-1]
            c.create_line(ex, ey, ex, ey-25, fill="#f8fafc", width=2)
            c.create_polygon(ex, ey-25, ex+18, ey-18, ex, ey-12, fill="#f8fafc", outline="#f8fafc")
            return

    def _write_report(self) -> None:
        if self.report_written:
            return
        self.report_path.parent.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(self.session.report(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        self.report_written = True
        print(f"report={self.report_path}")
        print(f"success={self.session.success}")
        print(f"fingerprint={self.session.spec.public_fingerprint()}")
        print(f"seed={self.session.spec.seed}")

    def _close(self) -> None:
        self._write_report()
        try:
            self.root.destroy()
        except tk.TclError:
            pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Ultra-light procedural Agent Interface control benchmark v1")
    parser.add_argument("--seed", type=int, default=None, help="Replay seed. Omit for a fresh hidden seed.")
    parser.add_argument("--difficulty", type=float, default=0.35, help="Convenience aggregate difficulty in [0,1].")
    parser.add_argument("--suite", choices=("core", "full"), default="full")
    parser.add_argument("--clock", choices=("realtime", "fixed"), default="realtime")
    parser.add_argument("--set", action="append", default=[], metavar="KEY=VALUE", help="Override one difficulty axis; repeatable.")
    parser.add_argument("--report", default="arena-v1-report.json")
    parser.add_argument("--autoclose", type=float, default=None, help="Close N seconds after completion.")
    args = parser.parse_args()

    overrides = _parse_overrides(args.set)
    profile = DifficultyProfile.from_level(args.difficulty).with_overrides(overrides)
    seed = fresh_seed() if args.seed is None else args.seed
    spec = generate_episode(seed, profile, suite=args.suite)
    session = BenchmarkSession(spec)
    root = tk.Tk()
    ArenaApp(root, session, Path(args.report), args.clock, args.autoclose)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
