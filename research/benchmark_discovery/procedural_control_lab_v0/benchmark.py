#!/usr/bin/env python3
"""Procedural Control Lab v0.

A tiny, stdlib-only real-time GUI benchmark for computer-control agents.
The controller should see only the rendered window and use ordinary keyboard/mouse
input. Hidden episode truth is retained for independent scoring and replay.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import secrets
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

WIDTH = 640
HEIGHT = 400
ARENA_TOP = 82
ARENA_BOTTOM = 392
COLORS = {
    "blue": "#3b82f6",
    "green": "#22c55e",
    "orange": "#f97316",
    "purple": "#a855f7",
    "red": "#ef4444",
    "yellow": "#eab308",
}
SHAPES = ("circle", "square", "triangle", "diamond")


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


@dataclass(frozen=True)
class Difficulty:
    level: float
    target_size: float
    target_speed: float
    distractors: int
    reaction_deadline_ms: int
    move_goal_size: float
    player_speed: float
    wait_ms: int
    typing_length: int
    instruction_font_px: int

    @classmethod
    def from_level(cls, level: float) -> "Difficulty":
        d = clamp(float(level), 0.0, 1.0)
        return cls(
            level=d,
            target_size=lerp(46.0, 14.0, d),
            target_speed=lerp(35.0, 260.0, d),
            distractors=int(round(2 + 8 * d)),
            reaction_deadline_ms=int(round(lerp(5000.0, 900.0, d))),
            move_goal_size=lerp(116.0, 42.0, d),
            player_speed=lerp(180.0, 120.0, d),
            wait_ms=int(round(lerp(450.0, 1350.0, d))),
            typing_length=int(round(3 + 7 * d)),
            instruction_font_px=int(round(lerp(18.0, 11.0, d))),
        )


@dataclass(frozen=True)
class ActorSpec:
    actor_id: str
    color: str
    shape: str
    x: float
    y: float
    vx: float
    vy: float
    is_target: bool


@dataclass(frozen=True)
class EpisodeSpec:
    schema: str
    seed: int
    run_id: str
    difficulty: Difficulty
    target_actor_id: str
    target_color: str
    target_shape: str
    actors: tuple[ActorSpec, ...]
    player_start: tuple[float, float]
    goal_rect: tuple[float, float, float, float]
    terminal_rect: tuple[float, float, float, float]
    typing_code: str
    global_timeout_ms: int
    instruction: str


def _hash_run(seed: int, difficulty: Difficulty) -> str:
    raw = json.dumps({"seed": seed, "difficulty": asdict(difficulty)}, sort_keys=True).encode()
    return hashlib.sha256(raw).hexdigest()[:16]


def generate_episode(seed: int, difficulty: Difficulty) -> EpisodeSpec:
    rng = random.Random(seed)
    target_color = rng.choice(tuple(COLORS))
    target_shape = rng.choice(SHAPES)
    run_id = _hash_run(seed, difficulty)

    goal_size = difficulty.move_goal_size
    gx = rng.uniform(20, WIDTH - goal_size - 20)
    gy = rng.uniform(ARENA_TOP + 18, ARENA_BOTTOM - goal_size - 18)
    goal = (gx, gy, gx + goal_size, gy + goal_size)

    px, py = WIDTH * 0.5, ARENA_BOTTOM - 34.0
    terminal_w, terminal_h = 142.0, 44.0
    terminal = (WIDTH - terminal_w - 12.0, ARENA_TOP + 8.0,
                WIDTH - 12.0, ARENA_TOP + 8.0 + terminal_h)

    count = 1 + difficulty.distractors
    actors: list[ActorSpec] = []
    used_pairs: set[tuple[str, str]] = set()
    for i in range(count):
        is_target = i == 0
        if is_target:
            color, shape = target_color, target_shape
        else:
            candidates = [(c, s) for c in COLORS for s in SHAPES
                          if (c, s) != (target_color, target_shape)]
            color, shape = rng.choice(candidates)
            # Duplicates are permitted only after exhausting easy visual distinctions.
            if (color, shape) in used_pairs and len(used_pairs) < len(candidates):
                for _ in range(40):
                    color, shape = rng.choice(candidates)
                    if (color, shape) not in used_pairs:
                        break
        used_pairs.add((color, shape))
        margin = difficulty.target_size + 12
        x = rng.uniform(margin, WIDTH - margin)
        y = rng.uniform(ARENA_TOP + margin, ARENA_BOTTOM - margin)
        angle = rng.uniform(0, math.tau)
        speed = difficulty.target_speed * rng.uniform(0.75, 1.05)
        actors.append(ActorSpec(
            actor_id=f"actor-{i}", color=color, shape=shape, x=x, y=y,
            vx=math.cos(angle) * speed, vy=math.sin(angle) * speed,
            is_target=is_target,
        ))

    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    code = "".join(rng.choice(alphabet) for _ in range(difficulty.typing_length))
    instruction = (
        f"WAIT for GO. MOVE into the outlined zone. CLICK the {target_color} "
        f"{target_shape}. Then CLICK TERMINAL and TYPE {code}, then Enter."
    )
    # Enough budget for the composed task while still exposing slow control.
    timeout = max(9000, difficulty.wait_ms + difficulty.reaction_deadline_ms * 3 + 5000)
    return EpisodeSpec(
        schema="procedural-control-lab-episode-v0",
        seed=seed,
        run_id=run_id,
        difficulty=difficulty,
        target_actor_id="actor-0",
        target_color=target_color,
        target_shape=target_shape,
        actors=tuple(actors),
        player_start=(px, py),
        goal_rect=goal,
        terminal_rect=terminal,
        typing_code=code,
        global_timeout_ms=timeout,
        instruction=instruction,
    )


@dataclass
class RuntimeActor:
    spec: ActorSpec
    x: float
    y: float
    vx: float
    vy: float


@dataclass
class Metrics:
    early_actions: int = 0
    wrong_clicks: int = 0
    typing_errors: int = 0
    key_events: int = 0
    pointer_clicks: int = 0
    action_count: int = 0
    wait_completed_ms: float | None = None
    move_completed_ms: float | None = None
    click_completed_ms: float | None = None
    typing_completed_ms: float | None = None
    first_move_latency_ms: float | None = None
    click_reaction_ms: float | None = None
    click_error_px: float | None = None


class ControlLabEngine:
    """Deterministic state machine driven by explicit simulation time and inputs."""

    def __init__(self, spec: EpisodeSpec):
        self.spec = spec
        self.now_ms = 0.0
        self.stage = "WAIT"
        self.stage_started_ms = 0.0
        self.player_x, self.player_y = spec.player_start
        self.held_keys: set[str] = set()
        self.actors = [RuntimeActor(a, a.x, a.y, a.vx, a.vy) for a in spec.actors]
        self.terminal_focused = False
        self.typed = ""
        self.metrics = Metrics()
        self.events: list[dict[str, Any]] = []
        self.violations: list[str] = []
        self.finished = False
        self.timed_out = False
        self._first_move_seen = False
        self._log("episode_start", stage=self.stage)

    def _log(self, kind: str, **payload: Any) -> None:
        self.events.append({"t_ms": round(self.now_ms, 3), "kind": kind, **payload})

    def _violate(self, name: str) -> None:
        self.violations.append(name)
        self._log("violation", name=name)

    def _transition(self, new_stage: str) -> None:
        self.stage = new_stage
        self.stage_started_ms = self.now_ms
        self._log("stage", stage=new_stage)

    def _advance_actors(self, dt_s: float) -> None:
        r = self.spec.difficulty.target_size * 0.5
        left, right = r + 2, WIDTH - r - 2
        top, bottom = ARENA_TOP + r + 2, ARENA_BOTTOM - r - 2
        for actor in self.actors:
            actor.x += actor.vx * dt_s
            actor.y += actor.vy * dt_s
            if actor.x < left:
                actor.x = left + (left - actor.x)
                actor.vx = abs(actor.vx)
            elif actor.x > right:
                actor.x = right - (actor.x - right)
                actor.vx = -abs(actor.vx)
            if actor.y < top:
                actor.y = top + (top - actor.y)
                actor.vy = abs(actor.vy)
            elif actor.y > bottom:
                actor.y = bottom - (actor.y - bottom)
                actor.vy = -abs(actor.vy)

    def _advance_player(self, dt_s: float) -> None:
        dx = ("d" in self.held_keys or "right" in self.held_keys) - ("a" in self.held_keys or "left" in self.held_keys)
        dy = ("s" in self.held_keys or "down" in self.held_keys) - ("w" in self.held_keys or "up" in self.held_keys)
        if dx or dy:
            mag = math.hypot(dx, dy)
            self.player_x += (dx / mag) * self.spec.difficulty.player_speed * dt_s
            self.player_y += (dy / mag) * self.spec.difficulty.player_speed * dt_s
            self.player_x = clamp(self.player_x, 8, WIDTH - 8)
            self.player_y = clamp(self.player_y, ARENA_TOP + 8, ARENA_BOTTOM - 8)
            if self.stage == "MOVE" and not self._first_move_seen:
                self._first_move_seen = True
                self.metrics.first_move_latency_ms = self.now_ms - self.stage_started_ms
                self._log("first_move")

    def _inside_goal(self) -> bool:
        x1, y1, x2, y2 = self.spec.goal_rect
        return x1 <= self.player_x <= x2 and y1 <= self.player_y <= y2

    def advance(self, dt_ms: float) -> None:
        if self.finished:
            return
        dt_ms = clamp(float(dt_ms), 0.0, 100.0)
        self.now_ms += dt_ms
        dt_s = dt_ms / 1000.0
        self._advance_actors(dt_s)
        self._advance_player(dt_s)

        if self.stage == "WAIT" and self.now_ms >= self.spec.difficulty.wait_ms:
            self.metrics.wait_completed_ms = self.now_ms
            self._transition("MOVE")
        if self.stage == "MOVE" and self._inside_goal():
            self.metrics.move_completed_ms = self.now_ms
            self._transition("CLICK")
        if self.stage == "CLICK" and self.now_ms - self.stage_started_ms > self.spec.difficulty.reaction_deadline_ms:
            self._violate("click_deadline_miss")
            self._finish(timeout=True)
        if self.stage == "TYPE" and self.now_ms - self.stage_started_ms > self.spec.difficulty.reaction_deadline_ms * 2:
            self._violate("typing_deadline_miss")
            self._finish(timeout=True)
        if self.now_ms > self.spec.global_timeout_ms:
            self._violate("global_timeout")
            self._finish(timeout=True)

    def key_down(self, key: str) -> None:
        if self.finished:
            return
        key = key.lower()
        self.metrics.key_events += 1
        self.metrics.action_count += 1
        self._log("key_down", key=key)
        if self.stage == "WAIT":
            self.metrics.early_actions += 1
            self._violate("input_during_wait")
        if self.stage == "TYPE":
            self._type_key(key)
            return
        self.held_keys.add(key)

    def key_up(self, key: str) -> None:
        if self.finished:
            return
        key = key.lower()
        self.metrics.key_events += 1
        self.metrics.action_count += 1
        self._log("key_up", key=key)
        if self.stage == "WAIT":
            self.metrics.early_actions += 1
            self._violate("input_during_wait")
        self.held_keys.discard(key)

    def _point_inside(self, x: float, y: float, rect: tuple[float, float, float, float]) -> bool:
        x1, y1, x2, y2 = rect
        return x1 <= x <= x2 and y1 <= y <= y2

    def click(self, x: float, y: float) -> None:
        if self.finished:
            return
        self.metrics.pointer_clicks += 1
        self.metrics.action_count += 1
        self._log("click", x=round(x, 2), y=round(y, 2), stage=self.stage)
        if self.stage == "WAIT":
            self.metrics.early_actions += 1
            self._violate("input_during_wait")
            return
        if self.stage == "CLICK":
            size = self.spec.difficulty.target_size
            hit: RuntimeActor | None = None
            nearest = float("inf")
            target_distance = None
            for actor in self.actors:
                dist = math.hypot(x - actor.x, y - actor.y)
                if actor.spec.is_target:
                    target_distance = dist
                if dist <= size * 0.5 and dist < nearest:
                    nearest, hit = dist, actor
            self.metrics.click_error_px = target_distance
            if hit is not None and hit.spec.actor_id == self.spec.target_actor_id:
                self.metrics.click_reaction_ms = self.now_ms - self.stage_started_ms
                self.metrics.click_completed_ms = self.now_ms
                self._log("target_hit", actor_id=hit.spec.actor_id)
                self._transition("TYPE")
            else:
                self.metrics.wrong_clicks += 1
                self._violate("wrong_or_missed_click")
            return
        if self.stage == "TYPE":
            self.terminal_focused = self._point_inside(x, y, self.spec.terminal_rect)
            self._log("terminal_focus", focused=self.terminal_focused)
            if not self.terminal_focused:
                self.metrics.wrong_clicks += 1
                self._violate("terminal_focus_miss")
            return
        # Clicking in MOVE is a forbidden side effect, even if harmless to locomotion.
        if self.stage == "MOVE":
            self.metrics.wrong_clicks += 1
            self._violate("unexpected_click_during_move")

    def _type_key(self, key: str) -> None:
        if not self.terminal_focused:
            # Movement keys after TYPE stage are not silently accepted as text.
            self.metrics.typing_errors += 1
            self._violate("typing_without_terminal_focus")
            return
        if key in ("return", "enter"):
            if self.typed == self.spec.typing_code:
                self.metrics.typing_completed_ms = self.now_ms
                self._log("typing_submit", correct=True)
                self._transition("DONE")
                self._finish(timeout=False)
            else:
                self.metrics.typing_errors += 1
                self._violate("incorrect_terminal_submit")
                self._log("typing_submit", correct=False, length=len(self.typed))
            return
        if key == "backspace":
            self.typed = self.typed[:-1]
            self._log("typed", length=len(self.typed))
            return
        if len(key) == 1 and key.isprintable():
            self.typed += key.upper()
            expected_prefix = self.spec.typing_code[:len(self.typed)]
            if self.typed != expected_prefix:
                self.metrics.typing_errors += 1
                self._violate("typing_mismatch")
            self._log("typed", length=len(self.typed))

    def _finish(self, timeout: bool) -> None:
        if self.finished:
            return
        self.finished = True
        self.timed_out = timeout
        self.held_keys.clear()
        self._log("episode_end", success=self.success)

    @property
    def success(self) -> bool:
        return self.stage == "DONE" and not self.violations and not self.timed_out

    def public_snapshot(self) -> dict[str, Any]:
        """State safe to expose to a benchmark harness; excludes oracle identity/seed."""
        return {
            "schema": "procedural-control-lab-public-v0",
            "run_id": self.spec.run_id,
            "stage": self.stage,
            "elapsed_ms": round(self.now_ms, 3),
            "finished": self.finished,
        }

    def result(self, reveal_private: bool = False) -> dict[str, Any]:
        data: dict[str, Any] = {
            "schema": "procedural-control-lab-result-v0",
            "run_id": self.spec.run_id,
            "difficulty": asdict(self.spec.difficulty),
            "success": self.success,
            "terminal_stage": self.stage,
            "elapsed_ms": round(self.now_ms, 3),
            "violations": list(self.violations),
            "metrics": asdict(self.metrics),
            "event_count": len(self.events),
        }
        if reveal_private:
            data["private"] = {
                "seed": self.spec.seed,
                "target_actor_id": self.spec.target_actor_id,
                "typing_code": self.spec.typing_code,
                "events": self.events,
            }
        return data


class TkControlLab:
    def __init__(self, engine: ControlLabEngine, result_path: Path | None,
                 private_log_path: Path | None, smoke_ms: int | None):
        import tkinter as tk

        self.tk = tk
        self.engine = engine
        self.result_path = result_path
        self.private_log_path = private_log_path
        self.smoke_ms = smoke_ms
        self.root = tk.Tk()
        self.root.title("Procedural Control Lab v0")
        self.root.geometry(f"{WIDTH}x{HEIGHT}")
        self.root.resizable(False, False)
        self.canvas = tk.Canvas(self.root, width=WIDTH, height=HEIGHT, bg="#101418", highlightthickness=0)
        self.canvas.pack()
        self.root.bind("<KeyPress>", self._on_key_down)
        self.root.bind("<KeyRelease>", self._on_key_up)
        self.root.bind("<Button-1>", self._on_click)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.canvas.focus_set()
        self.last_ns = time.monotonic_ns()
        self.started_ns = self.last_ns
        self.closed = False

    def _key_name(self, event: Any) -> str:
        key = event.keysym.lower()
        return "return" if key == "kp_enter" else key

    def _on_key_down(self, event: Any) -> None:
        self.engine.key_down(self._key_name(event))

    def _on_key_up(self, event: Any) -> None:
        self.engine.key_up(self._key_name(event))

    def _on_click(self, event: Any) -> None:
        self.engine.click(float(event.x), float(event.y))
        self.canvas.focus_set()

    def _draw_actor(self, actor: RuntimeActor, size: float) -> None:
        c = self.canvas
        x, y, r = actor.x, actor.y, size * 0.5
        fill = COLORS[actor.spec.color]
        if actor.spec.shape == "circle":
            c.create_oval(x-r, y-r, x+r, y+r, fill=fill, outline="#f8fafc", width=1)
        elif actor.spec.shape == "square":
            c.create_rectangle(x-r, y-r, x+r, y+r, fill=fill, outline="#f8fafc", width=1)
        elif actor.spec.shape == "triangle":
            c.create_polygon(x, y-r, x-r, y+r, x+r, y+r, fill=fill, outline="#f8fafc", width=1)
        else:
            c.create_polygon(x, y-r, x-r, y, x, y+r, x+r, y, fill=fill, outline="#f8fafc", width=1)

    def render(self) -> None:
        c = self.canvas
        c.delete("all")
        d = self.engine.spec.difficulty
        stage = self.engine.stage
        go = "GO" if stage != "WAIT" else "WAIT"
        c.create_text(10, 8, anchor="nw", fill="#f8fafc", font=("TkDefaultFont", d.instruction_font_px, "bold"),
                      text=self.engine.spec.instruction, width=620)
        c.create_text(10, 61, anchor="nw", fill="#93c5fd", font=("TkDefaultFont", 11, "bold"),
                      text=f"STATE: {go}   STAGE: {stage}")
        c.create_line(0, ARENA_TOP-2, WIDTH, ARENA_TOP-2, fill="#475569")

        x1, y1, x2, y2 = self.engine.spec.goal_rect
        c.create_rectangle(x1, y1, x2, y2, outline="#e2e8f0", width=2, dash=(5, 3))
        c.create_text((x1+x2)/2, y1+11, text="GOAL", fill="#cbd5e1", font=("TkDefaultFont", 9, "bold"))

        tx1, ty1, tx2, ty2 = self.engine.spec.terminal_rect
        terminal_fill = "#334155" if not self.engine.terminal_focused else "#475569"
        c.create_rectangle(tx1, ty1, tx2, ty2, fill=terminal_fill, outline="#94a3b8", width=2)
        shown = self.engine.typed if self.engine.terminal_focused else "TERMINAL"
        c.create_text((tx1+tx2)/2, (ty1+ty2)/2, text=shown, fill="#f8fafc", font=("TkFixedFont", 11, "bold"))

        for actor in self.engine.actors:
            self._draw_actor(actor, d.target_size)

        p = 8
        c.create_polygon(self.engine.player_x, self.engine.player_y-p,
                         self.engine.player_x-p, self.engine.player_y+p,
                         self.engine.player_x+p, self.engine.player_y+p,
                         fill="#f8fafc", outline="#0f172a")

        if self.engine.finished:
            label = "PASS" if self.engine.success else "FAIL"
            c.create_rectangle(170, 150, 470, 250, fill="#111827", outline="#e2e8f0", width=2)
            c.create_text(320, 185, text=label, fill="#f8fafc", font=("TkDefaultFont", 28, "bold"))
            c.create_text(320, 225, text=f"run {self.engine.spec.run_id}", fill="#cbd5e1", font=("TkFixedFont", 10))

    def tick(self) -> None:
        if self.closed:
            return
        now = time.monotonic_ns()
        dt_ms = (now - self.last_ns) / 1_000_000.0
        self.last_ns = now
        self.engine.advance(dt_ms)
        self.render()
        wall_ms = (now - self.started_ns) / 1_000_000.0
        if self.engine.finished or (self.smoke_ms is not None and wall_ms >= self.smoke_ms):
            self.close()
            return
        self.root.after(16, self.tick)

    def close(self) -> None:
        if self.closed:
            return
        self.closed = True
        result = self.engine.result(reveal_private=False)
        if self.result_path:
            self.result_path.parent.mkdir(parents=True, exist_ok=True)
            self.result_path.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        if self.private_log_path:
            private = self.engine.result(reveal_private=True)
            self.private_log_path.parent.mkdir(parents=True, exist_ok=True)
            self.private_log_path.write_text(json.dumps(private, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        try:
            self.root.destroy()
        except Exception:
            pass

    def run(self) -> int:
        self.render()
        self.root.after(16, self.tick)
        self.root.mainloop()
        return 0


def drive_perfect_headless(engine: ControlLabEngine) -> None:
    """Positive-control oracle used only for construction tests, never agent evaluation."""
    while engine.stage == "WAIT" and not engine.finished:
        engine.advance(10)
    # Locomotion through ordinary key state transitions.
    while engine.stage == "MOVE" and not engine.finished:
        x1, y1, x2, y2 = engine.spec.goal_rect
        tx, ty = (x1+x2)/2, (y1+y2)/2
        keys: list[str] = []
        if engine.player_x < tx - 2:
            keys.append("d")
        elif engine.player_x > tx + 2:
            keys.append("a")
        if engine.player_y < ty - 2:
            keys.append("s")
        elif engine.player_y > ty + 2:
            keys.append("w")
        for k in keys:
            if k not in engine.held_keys:
                engine.key_down(k)
        for k in list(engine.held_keys):
            if k not in keys:
                engine.key_up(k)
        engine.advance(10)
    for k in list(engine.held_keys):
        engine.key_up(k)
    if engine.stage == "CLICK":
        target = next(a for a in engine.actors if a.spec.actor_id == engine.spec.target_actor_id)
        engine.click(target.x, target.y)
    if engine.stage == "TYPE":
        x1, y1, x2, y2 = engine.spec.terminal_rect
        engine.click((x1+x2)/2, (y1+y2)/2)
        for ch in engine.spec.typing_code:
            engine.key_down(ch.lower())
        engine.key_down("return")


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--difficulty", type=float, default=0.35, help="continuous 0..1 difficulty")
    p.add_argument("--seed", type=int, default=None, help="dev/replay seed; omit for fresh hidden seed")
    p.add_argument("--reveal-seed", action="store_true", help="dev only: print seed")
    p.add_argument("--mode", choices=("gui", "headless-perfect"), default="gui")
    p.add_argument("--result", type=Path, default=None, help="public result JSON")
    p.add_argument("--private-log", type=Path, default=None, help="private oracle/event JSON")
    p.add_argument("--smoke-ms", type=int, default=None, help="GUI construction smoke: exit after N wall ms")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    difficulty = Difficulty.from_level(args.difficulty)
    seed = args.seed if args.seed is not None else secrets.randbits(63)
    spec = generate_episode(seed, difficulty)
    engine = ControlLabEngine(spec)
    info = {"schema": "procedural-control-lab-launch-v0", "run_id": spec.run_id, "difficulty": difficulty.level}
    if args.reveal_seed:
        info["seed"] = seed
    print(json.dumps(info, sort_keys=True), flush=True)

    if args.mode == "headless-perfect":
        drive_perfect_headless(engine)
        result = engine.result(reveal_private=args.reveal_seed)
        if args.result:
            args.result.parent.mkdir(parents=True, exist_ok=True)
            args.result.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, sort_keys=True), flush=True)
        return 0 if engine.success else 2

    app = TkControlLab(engine, args.result, args.private_log, args.smoke_ms)
    return app.run()


if __name__ == "__main__":
    raise SystemExit(main())
