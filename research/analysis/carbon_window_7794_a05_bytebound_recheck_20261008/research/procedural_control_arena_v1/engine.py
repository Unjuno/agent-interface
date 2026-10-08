from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields, replace
import hashlib
import json
import math
import random
import secrets
import string
import time
from typing import Any

WIDTH = 720
HEIGHT = 520
HUD_HEIGHT = 110
PLAY_TOP = HUD_HEIGHT
PLAY_BOTTOM = HEIGHT - 18
TICK_HZ = 60.0

COLORS = ("blue", "red", "green", "yellow", "purple", "orange")
SHAPES = ("circle", "square", "triangle", "diamond")
FULL_PRIMITIVES = ("move", "target", "switch", "typing", "combo", "drag", "assembly", "trace", "recovery")
CORE_PRIMITIVES = ("move", "target", "switch", "typing")


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


@dataclass(frozen=True)
class DifficultyProfile:
    level: float
    target_radius: float
    target_speed: float
    distractor_count: int
    visual_similarity: float
    move_zone_radius: float
    move_deadline: float
    target_deadline: float
    switch_wait: float
    switch_deadline: float
    typing_length: int
    typing_deadline: float
    objective_sample_radius: float
    drag_radius: float
    drag_tolerance: float
    drag_deadline: float
    assembly_pieces: int
    assembly_tolerance: float
    assembly_deadline: float
    combo_deadline: float
    trace_tolerance: float
    trace_checkpoints: int
    trace_deadline: float
    recovery_deadline: float
    recovery_displacement: float

    @classmethod
    def from_level(cls, level: float) -> "DifficultyProfile":
        d = _clamp(float(level), 0.0, 1.0)
        return cls(
            level=d,
            target_radius=_lerp(34.0, 10.0, d),
            target_speed=_lerp(0.0, 190.0, d),
            distractor_count=int(round(_lerp(2.0, 11.0, d))),
            visual_similarity=_lerp(0.05, 0.9, d),
            move_zone_radius=_lerp(72.0, 24.0, d),
            move_deadline=_lerp(10.0, 3.8, d),
            target_deadline=_lerp(8.0, 2.3, d),
            switch_wait=_lerp(2.2, 0.55, d),
            switch_deadline=_lerp(6.0, 2.0, d),
            typing_length=int(round(_lerp(3.0, 11.0, d))),
            typing_deadline=_lerp(10.0, 3.5, d),
            objective_sample_radius=_lerp(24.0, 14.0, d),
            drag_radius=_lerp(30.0, 14.0, d),
            drag_tolerance=_lerp(42.0, 10.0, d),
            drag_deadline=_lerp(9.0, 3.0, d),
            assembly_pieces=int(round(_lerp(2.0, 6.0, d))),
            assembly_tolerance=_lerp(40.0, 10.0, d),
            assembly_deadline=_lerp(15.0, 5.0, d),
            combo_deadline=_lerp(8.0, 2.4, d),
            trace_tolerance=_lerp(24.0, 6.0, d),
            trace_checkpoints=int(round(_lerp(4.0, 10.0, d))),
            trace_deadline=_lerp(12.0, 4.0, d),
            recovery_deadline=_lerp(10.0, 3.0, d),
            recovery_displacement=_lerp(90.0, 260.0, d),
        )

    def with_overrides(self, overrides: dict[str, float | int]) -> "DifficultyProfile":
        valid = {f.name: f for f in fields(self) if f.name != "level"}
        unknown = sorted(set(overrides) - set(valid))
        if unknown:
            raise ValueError(f"unknown difficulty override(s): {', '.join(unknown)}")
        values: dict[str, Any] = {}
        for key, raw in overrides.items():
            current = getattr(self, key)
            if isinstance(current, int) and not isinstance(current, bool):
                values[key] = int(raw)
            else:
                values[key] = float(raw)
        candidate = replace(self, **values)
        if candidate.target_radius <= 1 or candidate.drag_radius <= 1 or candidate.objective_sample_radius <= 2:
            raise ValueError("radius overrides must be > minimum")
        if candidate.distractor_count < 0 or candidate.assembly_pieces < 1 or candidate.trace_checkpoints < 2:
            raise ValueError("count overrides outside valid range")
        if not 0.0 <= candidate.visual_similarity <= 1.0:
            raise ValueError("visual_similarity must be in [0,1]")
        if candidate.switch_wait < 0 or candidate.recovery_displacement < 0:
            raise ValueError("wait/displacement overrides must be >= 0")
        if candidate.typing_length < 1:
            raise ValueError("typing_length override outside valid range")
        for key in ("drag_tolerance", "assembly_tolerance", "trace_tolerance"):
            if getattr(candidate, key) <= 0:
                raise ValueError(f"{key} must be > 0")
        for key in ("move_deadline", "target_deadline", "switch_deadline", "typing_deadline", "drag_deadline", "assembly_deadline", "combo_deadline", "trace_deadline", "recovery_deadline"):
            if getattr(candidate, key) <= 0:
                raise ValueError(f"{key} must be > 0")
        return candidate


@dataclass(frozen=True)
class ObjectSpec:
    object_id: str
    color: str
    shape: str
    x: float
    y: float
    vx: float
    vy: float
    radius: float


@dataclass(frozen=True)
class StageSpec:
    kind: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class EpisodeSpec:
    schema: str
    seed: int
    suite: str
    difficulty: DifficultyProfile
    stages: tuple[StageSpec, ...]

    def public_fingerprint(self) -> str:
        payload = self.to_dict(include_seed=False)
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(raw).hexdigest()[:16]

    def to_dict(self, *, include_seed: bool) -> dict[str, Any]:
        data = {
            "schema": self.schema,
            "suite": self.suite,
            "difficulty": asdict(self.difficulty),
            "stages": [asdict(s) for s in self.stages],
        }
        if include_seed:
            data["seed"] = self.seed
        return data

    def canonical_json(self, *, include_seed: bool = True) -> str:
        return json.dumps(self.to_dict(include_seed=include_seed), sort_keys=True, separators=(",", ":"))


def fresh_seed() -> int:
    return secrets.randbits(63)


def _safe_point(rng: random.Random, margin: float) -> tuple[float, float]:
    return (
        rng.uniform(margin, WIDTH - margin),
        rng.uniform(PLAY_TOP + margin, PLAY_BOTTOM - margin),
    )


def _velocity(rng: random.Random, speed: float) -> tuple[float, float]:
    if speed <= 0:
        return 0.0, 0.0
    angle = rng.uniform(0.0, math.tau)
    magnitude = rng.uniform(speed * 0.55, speed)
    return math.cos(angle) * magnitude, math.sin(angle) * magnitude


def _semantic_distractor(rng: random.Random, target: tuple[str, str], similarity: float) -> tuple[str, str]:
    color, shape = target
    if rng.random() < similarity:
        if rng.random() < 0.5:
            return color, rng.choice(tuple(s for s in SHAPES if s != shape))
        return rng.choice(tuple(c for c in COLORS if c != color)), shape
    pool = [(c, s) for c in COLORS for s in SHAPES if (c, s) != target and c != color and s != shape]
    return rng.choice(pool or [(c, s) for c in COLORS for s in SHAPES if (c, s) != target])


def _object_cloud(rng: random.Random, d: DifficultyProfile, *, target_count: int = 1) -> tuple[list[ObjectSpec], list[str]]:
    target_semantics = rng.sample([(c, s) for c in COLORS for s in SHAPES], k=target_count)
    specs: list[ObjectSpec] = []
    target_ids: list[str] = []
    total = target_count + d.distractor_count
    for idx in range(total):
        if idx < target_count:
            color, shape = target_semantics[idx]
            target_ids.append(f"obj-{idx}")
        else:
            color, shape = _semantic_distractor(rng, target_semantics[0], d.visual_similarity)
        margin = d.target_radius + 8
        x = y = 0.0
        for _ in range(128):
            x, y = _safe_point(rng, margin)
            if all(math.hypot(x - other.x, y - other.y) >= d.target_radius * 2.25 for other in specs):
                break
        vx, vy = _velocity(rng, d.target_speed)
        specs.append(ObjectSpec(f"obj-{idx}", color, shape, x, y, vx, vy, d.target_radius))
    return specs, target_ids


def _target_payload(rng: random.Random, d: DifficultyProfile, *, switch: bool = False, combo: bool = False, recovery: bool = False) -> dict[str, Any]:
    target_count = 2 if switch else 1
    objects, targets = _object_cloud(rng, d, target_count=target_count)
    if switch:
        return {
            "objects": [asdict(o) for o in objects],
            "prepared_id": targets[0],
            "active_id": targets[1],
            "wait_seconds": d.switch_wait,
            "deadline": d.switch_deadline,
        }
    payload: dict[str, Any] = {
        "objects": [asdict(o) for o in objects],
        "target_id": targets[0],
        "deadline": d.target_deadline,
    }
    if combo:
        payload["required_key"] = rng.choice(("space", "shift"))
        payload["deadline"] = d.combo_deadline
    if recovery:
        payload["deadline"] = d.recovery_deadline
        target = next(o for o in objects if o.object_id == targets[0])
        rx, ry = target.x, target.y
        min_disp = min(d.recovery_displacement, math.hypot(WIDTH, PLAY_BOTTOM - PLAY_TOP) * 0.55)
        for _ in range(256):
            cx = rng.uniform(d.target_radius + 12, WIDTH - d.target_radius - 12)
            cy = rng.uniform(PLAY_TOP + d.target_radius + 12, PLAY_BOTTOM - d.target_radius - 12)
            rx, ry = cx, cy
            if math.hypot(rx - target.x, ry - target.y) >= min_disp:
                break
        payload["recovery_x"] = rx
        payload["recovery_y"] = ry
        payload["recovery_displacement"] = math.hypot(rx - target.x, ry - target.y)
    return payload


def _drag_payload(rng: random.Random, d: DifficultyProfile) -> dict[str, Any]:
    color = rng.choice(COLORS)
    shape = rng.choice(SHAPES)
    radius = d.drag_radius
    sx, sy = _safe_point(rng, radius + 14)
    dx, dy = _safe_point(rng, radius + 50)
    for _ in range(128):
        if math.hypot(dx - sx, dy - sy) >= 180:
            break
        dx, dy = _safe_point(rng, radius + 50)
    return {
        "piece": asdict(ObjectSpec("drag-piece", color, shape, sx, sy, 0.0, 0.0, radius)),
        "slot_x": dx,
        "slot_y": dy,
        "tolerance": d.drag_tolerance,
        "deadline": d.drag_deadline,
    }


def _assembly_payload(rng: random.Random, d: DifficultyProfile) -> dict[str, Any]:
    count = min(d.assembly_pieces, len(COLORS) * len(SHAPES))
    semantics = rng.sample([(c, s) for c in COLORS for s in SHAPES], k=count)
    pieces: list[ObjectSpec] = []
    slots: list[dict[str, Any]] = []
    radius = max(12.0, d.drag_radius * 0.78)
    left_band = (20, WIDTH * 0.44)
    right_band = (WIDTH * 0.56, WIDTH - 20)
    used_piece: list[tuple[float, float]] = []
    used_slot: list[tuple[float, float]] = []
    for idx, (color, shape) in enumerate(semantics):
        px = py = sx = sy = 0.0
        for _ in range(128):
            px = rng.uniform(left_band[0] + radius, left_band[1] - radius)
            py = rng.uniform(PLAY_TOP + radius + 10, PLAY_BOTTOM - radius - 10)
            if all(math.hypot(px-x, py-y) >= radius*2.4 for x, y in used_piece):
                break
        used_piece.append((px, py))
        for _ in range(128):
            sx = rng.uniform(right_band[0] + radius, right_band[1] - radius)
            sy = rng.uniform(PLAY_TOP + radius + 10, PLAY_BOTTOM - radius - 10)
            if all(math.hypot(sx-x, sy-y) >= radius*2.4 for x, y in used_slot):
                break
        used_slot.append((sx, sy))
        pid = f"piece-{idx}"
        pieces.append(ObjectSpec(pid, color, shape, px, py, 0.0, 0.0, radius))
        slots.append({"piece_id": pid, "color": color, "shape": shape, "x": sx, "y": sy, "radius": radius})
    return {
        "pieces": [asdict(p) for p in pieces],
        "slots": slots,
        "tolerance": d.assembly_tolerance,
        "deadline": d.assembly_deadline,
    }


def _trace_payload(rng: random.Random, d: DifficultyProfile) -> dict[str, Any]:
    count = d.trace_checkpoints
    margin = 42.0
    start_x = rng.uniform(margin, WIDTH * 0.25)
    end_x = rng.uniform(WIDTH * 0.75, WIDTH - margin)
    xs = [start_x + (end_x - start_x) * i / (count - 1) for i in range(count)]
    base = rng.uniform(PLAY_TOP + 80, PLAY_BOTTOM - 80)
    amplitude = rng.uniform(30, min(110, (PLAY_BOTTOM-PLAY_TOP)/3))
    phase = rng.uniform(0, math.tau)
    points = []
    for i, x in enumerate(xs):
        y = base + amplitude * math.sin(phase + i * rng.uniform(0.7, 1.2))
        y = _clamp(y, PLAY_TOP + margin, PLAY_BOTTOM - margin)
        points.append((round(x, 3), round(y, 3)))
    return {
        "points": points,
        "tolerance": d.trace_tolerance,
        "deadline": d.trace_deadline,
    }


def generate_episode(seed: int, difficulty: float | DifficultyProfile, suite: str = "full") -> EpisodeSpec:
    rng = random.Random(int(seed))
    d = difficulty if isinstance(difficulty, DifficultyProfile) else DifficultyProfile.from_level(difficulty)
    if suite not in {"core", "full"}:
        raise ValueError("suite must be core or full")
    code_alphabet = string.ascii_uppercase + string.digits
    code = "".join(rng.choice(code_alphabet) for _ in range(d.typing_length))
    terminal_w = _lerp(200.0, 126.0, d.level)
    terminal_h = _lerp(70.0, 46.0, d.level)
    terminal_x = rng.uniform(20.0, WIDTH - terminal_w - 20.0)
    terminal_y = rng.uniform(PLAY_TOP + 24.0, PLAY_BOTTOM - terminal_h - 10.0)
    zone_x, zone_y = _safe_point(rng, d.move_zone_radius + 12)

    builders: dict[str, StageSpec] = {
        "move": StageSpec("move", {"zone_x": zone_x, "zone_y": zone_y, "zone_radius": d.move_zone_radius, "deadline": d.move_deadline}),
        "target": StageSpec("target", _target_payload(rng, d)),
        "switch": StageSpec("switch", _target_payload(rng, d, switch=True)),
        "typing": StageSpec("typing", {"code": code, "terminal_x": terminal_x, "terminal_y": terminal_y, "terminal_w": terminal_w, "terminal_h": terminal_h, "deadline": d.typing_deadline}),
        "combo": StageSpec("combo", _target_payload(rng, d, combo=True)),
        "drag": StageSpec("drag", _drag_payload(rng, d)),
        "assembly": StageSpec("assembly", _assembly_payload(rng, d)),
        "trace": StageSpec("trace", _trace_payload(rng, d)),
        "recovery": StageSpec("recovery", _target_payload(rng, d, recovery=True)),
    }
    names = list(CORE_PRIMITIVES if suite == "core" else FULL_PRIMITIVES)
    rng.shuffle(names)
    return EpisodeSpec("procedural-control-arena-v1", int(seed), suite, d, tuple(builders[n] for n in names))


@dataclass
class RuntimeObject:
    object_id: str
    color: str
    shape: str
    x: float
    y: float
    vx: float
    vy: float
    radius: float
    locked: bool = False

    @classmethod
    def from_spec(cls, spec: dict[str, Any]) -> "RuntimeObject":
        return cls(**spec)

    def step(self, dt: float) -> None:
        if self.locked:
            return
        self.x += self.vx * dt
        self.y += self.vy * dt
        left, right = self.radius, WIDTH - self.radius
        top, bottom = PLAY_TOP + self.radius, PLAY_BOTTOM - self.radius
        if self.x < left:
            self.x = left + (left - self.x)
            self.vx = abs(self.vx)
        elif self.x > right:
            self.x = right - (self.x - right)
            self.vx = -abs(self.vx)
        if self.y < top:
            self.y = top + (top - self.y)
            self.vy = abs(self.vy)
        elif self.y > bottom:
            self.y = bottom - (self.y - bottom)
            self.vy = -abs(self.vy)


@dataclass
class SessionEvent:
    sim_time: float
    wall_offset: float
    stage_index: int
    event: str
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class Metrics:
    actions: int = 0
    key_events: int = 0
    pointer_downs: int = 0
    pointer_moves: int = 0
    pointer_ups: int = 0
    wrong_targets: int = 0
    motor_misses: int = 0
    stale_actions: int = 0
    premature_actions: int = 0
    typing_errors: int = 0
    drag_misses: int = 0
    assembly_misses: int = 0
    trace_deviations: int = 0
    recovery_events: int = 0
    recovery_successes: int = 0
    completed_stages: int = 0


class BenchmarkSession:
    """Hidden-oracle benchmark state machine. Controller-facing state excludes seed and IDs."""

    def __init__(self, spec: EpisodeSpec):
        self.spec = spec
        self.started_wall = time.monotonic()
        self.sim_time = 0.0
        self.stage_started = 0.0
        self.stage_index = 0
        self.done = False
        self.success = False
        self.failure_reason: str | None = None
        self.failure_locus: str | None = None
        self.events: list[SessionEvent] = []
        self.metrics = Metrics()
        self.keys_down: set[str] = set()
        self.player_x = WIDTH / 2.0
        self.player_y = (PLAY_TOP + PLAY_BOTTOM) / 2.0
        self.player_speed = 180.0
        self.objects: list[RuntimeObject] = []
        self.terminal_focused = False
        self.text_buffer = ""
        self.drag_object_id: str | None = None
        self.pointer_stage_index: int | None = None
        self.trace_started = False
        self.trace_checkpoint = 0
        self.recovery_triggered = False
        self.assembly_locked: set[str] = set()
        self.stage_results: list[dict[str, Any]] = []
        self._load_stage()
        self._event("episode_start", {"fingerprint": spec.public_fingerprint(), "suite": spec.suite})

    @property
    def stage(self) -> StageSpec:
        return self.spec.stages[self.stage_index]

    @property
    def stage_elapsed(self) -> float:
        return self.sim_time - self.stage_started

    def _event(self, name: str, detail: dict[str, Any] | None = None) -> None:
        self.events.append(SessionEvent(round(self.sim_time, 6), round(time.monotonic() - self.started_wall, 6), self.stage_index, name, detail or {}))

    def _load_stage(self) -> None:
        if self.stage_index >= len(self.spec.stages):
            self.done = True
            self.success = True
            return
        self.stage_started = self.sim_time
        self.keys_down.clear()
        self.terminal_focused = False
        self.text_buffer = ""
        self.drag_object_id = None
        self.pointer_stage_index = None
        self.trace_started = False
        self.trace_checkpoint = 0
        self.recovery_triggered = False
        self.assembly_locked = set()
        p = self.stage.payload
        object_specs = p.get("objects") or p.get("pieces") or ([p["piece"]] if "piece" in p else [])
        self.objects = [RuntimeObject.from_spec(o) for o in object_specs]
        self._event("stage_start", {"kind": self.stage.kind})

    def _complete_stage(self, detail: dict[str, Any] | None = None) -> None:
        if self.done:
            return
        elapsed = self.stage_elapsed
        kind = self.stage.kind
        self.stage_results.append({"stage": kind, "success": True, "duration": round(elapsed, 6), **(detail or {})})
        self.metrics.completed_stages += 1
        self._event("stage_success", detail or {})
        self.stage_index += 1
        if self.stage_index >= len(self.spec.stages):
            self.done = True
            self.success = True
            self.keys_down.clear()
            self._event("episode_success", {})
            return
        self._load_stage()

    def _fail(self, reason: str, locus: str, detail: dict[str, Any] | None = None) -> None:
        if self.done:
            return
        self.failure_reason = reason
        self.failure_locus = locus
        self.done = True
        self.success = False
        self.keys_down.clear()
        self.stage_results.append({"stage": self.stage.kind, "success": False, "duration": round(self.stage_elapsed, 6), "reason": reason, "locus": locus})
        self._event("episode_failure", {"reason": reason, "locus": locus, **(detail or {})})

    def deadline(self) -> float:
        return float(self.stage.payload["deadline"])

    def public_state(self) -> dict[str, Any]:
        """Minimal transport state; task semantics remain in rendered pixels."""
        return {
            "schema": "procedural-control-arena-public-v1",
            "sim_time": round(self.sim_time, 6),
            "done": self.done,
        }

    def _object_by_id(self, object_id: str) -> RuntimeObject:
        for obj in self.objects:
            if obj.object_id == object_id:
                return obj
        raise KeyError(object_id)

    @staticmethod
    def _contains(obj: RuntimeObject, x: float, y: float) -> bool:
        dx, dy, r = x - obj.x, y - obj.y, obj.radius
        if obj.shape == "circle":
            return dx*dx + dy*dy <= r*r
        if obj.shape == "square":
            return abs(dx) <= r and abs(dy) <= r
        if obj.shape == "diamond":
            return abs(dx) + abs(dy) <= r
        if obj.shape == "triangle":
            return -r <= dy <= r and abs(dx) <= (dy + r) / 2.0
        return False

    def _object_at(self, x: float, y: float) -> RuntimeObject | None:
        candidates = [(math.hypot(o.x-x, o.y-y), o) for o in self.objects if not o.locked and self._contains(o, x, y)]
        if not candidates:
            return None
        candidates.sort(key=lambda v: v[0])
        return candidates[0][1]

    def step(self, dt: float) -> None:
        if self.done:
            return
        dt = _clamp(float(dt), 0.0, 0.1)
        self.sim_time += dt
        for obj in self.objects:
            obj.step(dt)
        if self.stage.kind == "move":
            dx = (1 if "d" in self.keys_down else 0) - (1 if "a" in self.keys_down else 0)
            dy = (1 if "s" in self.keys_down else 0) - (1 if "w" in self.keys_down else 0)
            if dx or dy:
                norm = math.hypot(dx, dy)
                self.player_x = _clamp(self.player_x + self.player_speed * dt * dx / norm, 10.0, WIDTH - 10.0)
                self.player_y = _clamp(self.player_y + self.player_speed * dt * dy / norm, PLAY_TOP + 10.0, PLAY_BOTTOM - 10.0)
            p = self.stage.payload
            if math.hypot(self.player_x-p["zone_x"], self.player_y-p["zone_y"]) <= p["zone_radius"]:
                self._complete_stage({"motor": "move"})
                return
        if self.stage_elapsed > self.deadline():
            self._fail("deadline_miss", "REALTIME_DEADLINE", {"stage": self.stage.kind})

    def key_down(self, key: str) -> None:
        if self.done:
            return
        key = key.lower()
        self.metrics.actions += 1
        self.metrics.key_events += 1
        self.keys_down.add(key)
        self._event("key_down", {"key": key})

    def key_up(self, key: str) -> None:
        key = key.lower()
        if key in self.keys_down:
            self.metrics.actions += 1
            self.metrics.key_events += 1
            self.keys_down.remove(key)
            self._event("key_up", {"key": key})

    def _semantic_hit(self, x: float, y: float, target_id: str, *, stage: str) -> bool:
        hit = self._object_at(x, y)
        if hit is None:
            self.metrics.motor_misses += 1
            self._fail("motor_miss", "MOTOR", {"stage": stage})
            return False
        if hit.object_id != target_id:
            self.metrics.wrong_targets += 1
            self._fail("wrong_target", "CONTROLLER_DECISION", {"semantic": f"{hit.color}:{hit.shape}"})
            return False
        return True

    def pointer_down(self, x: float, y: float) -> None:
        if self.done:
            return
        self.metrics.actions += 1
        self.metrics.pointer_downs += 1
        self.pointer_stage_index = self.stage_index
        self._event("pointer_down", {"x": round(x,2), "y": round(y,2)})
        p, kind = self.stage.payload, self.stage.kind
        if kind == "target":
            if self._semantic_hit(x, y, p["target_id"], stage="target"):
                self._complete_stage({"motor": "pointer"})
            return
        if kind == "combo":
            required = str(p["required_key"]).lower()
            if required not in self.keys_down:
                self._fail("missing_chord", "MOTOR", {"required_key": required})
                return
            if self._semantic_hit(x, y, p["target_id"], stage="combo"):
                self._complete_stage({"motor": "keyboard+pointer", "required_key": required})
            return
        if kind == "switch":
            hit = self._object_at(x, y)
            if self.stage_elapsed < float(p["wait_seconds"]):
                self.metrics.premature_actions += 1
                self._fail("premature_action", "CONTROLLER_DECISION", {"hit": None if hit is None else f"{hit.color}:{hit.shape}"})
                return
            if hit is None:
                self.metrics.motor_misses += 1
                self._fail("motor_miss", "MOTOR", {"stage": "switch"})
            elif hit.object_id == p["active_id"]:
                self._complete_stage({"freshness": "switch_accepted"})
            elif hit.object_id == p["prepared_id"]:
                self.metrics.stale_actions += 1
                self._fail("stale_action", "STALE_STATE", {"semantic": f"{hit.color}:{hit.shape}"})
            else:
                self.metrics.wrong_targets += 1
                self._fail("wrong_target", "CONTROLLER_DECISION", {"semantic": f"{hit.color}:{hit.shape}"})
            return
        if kind == "typing":
            tx, ty, tw, th = p["terminal_x"], p["terminal_y"], p["terminal_w"], p["terminal_h"]
            self.terminal_focused = tx <= x <= tx+tw and ty <= y <= ty+th
            self._event("terminal_focus", {"focused": self.terminal_focused})
            return
        if kind in {"drag", "assembly"}:
            hit = self._object_at(x, y)
            if hit is None:
                if kind == "drag": self.metrics.drag_misses += 1
                else: self.metrics.assembly_misses += 1
                self._fail("drag_pickup_miss", "MOTOR", {"stage": kind})
                return
            self.drag_object_id = hit.object_id
            self._event("drag_start", {"semantic": f"{hit.color}:{hit.shape}"})
            return
        if kind == "trace":
            points = p["points"]
            sx, sy = points[0]
            if math.hypot(x-sx, y-sy) > p["tolerance"]:
                self.metrics.trace_deviations += 1
                self._fail("trace_start_miss", "MOTOR", {})
                return
            self.trace_started = True
            self.trace_checkpoint = 0
            self._event("trace_start", {})
            return
        if kind == "recovery":
            if not self._semantic_hit(x, y, p["target_id"], stage="recovery"):
                return
            target = self._object_by_id(p["target_id"])
            if not self.recovery_triggered:
                self.recovery_triggered = True
                self.metrics.recovery_events += 1
                target.x = float(p["recovery_x"])
                target.y = float(p["recovery_y"])
                target.vx, target.vy = _velocity(random.Random(self.spec.seed ^ 0xA5A5A5A5), self.spec.difficulty.target_speed)
                self._event("recovery_interrupt", {"kind": "target_relocated"})
            else:
                self.metrics.recovery_successes += 1
                self._complete_stage({"recovery": "reacquired"})
            return
        if kind == "move":
            self._event("irrelevant_pointer", {"stage": kind})

    def pointer_move(self, x: float, y: float) -> None:
        if self.done:
            return
        self.metrics.pointer_moves += 1
        kind, p = self.stage.kind, self.stage.payload
        if kind in {"drag", "assembly"} and self.drag_object_id is not None:
            obj = self._object_by_id(self.drag_object_id)
            obj.x = _clamp(x, obj.radius, WIDTH-obj.radius)
            obj.y = _clamp(y, PLAY_TOP+obj.radius, PLAY_BOTTOM-obj.radius)
            self._event("drag_move", {"x": round(obj.x,1), "y": round(obj.y,1)})
            return
        if kind == "trace" and self.trace_started:
            points = p["points"]
            next_idx = min(self.trace_checkpoint + 1, len(points)-1)
            nx, ny = points[next_idx]
            # Require ordered checkpoint coverage; this makes path quality diagnosable.
            if math.hypot(x-nx, y-ny) <= p["tolerance"]:
                self.trace_checkpoint = next_idx
                self._event("trace_checkpoint", {"index": next_idx})
            else:
                # Distance to either current or next checkpoint must remain bounded.
                cx, cy = points[self.trace_checkpoint]
                if min(math.hypot(x-cx, y-cy), math.hypot(x-nx, y-ny)) > p["tolerance"] * 1.8:
                    self.metrics.trace_deviations += 1
                    self._fail("trace_deviation", "MOTOR", {"checkpoint": self.trace_checkpoint})

    def pointer_up(self, x: float, y: float) -> None:
        if self.done:
            return
        if self.pointer_stage_index is not None and self.pointer_stage_index != self.stage_index:
            self.pointer_stage_index = None
            return
        self.metrics.actions += 1
        self.metrics.pointer_ups += 1
        self._event("pointer_up", {"x": round(x,2), "y": round(y,2)})
        p, kind = self.stage.payload, self.stage.kind
        if kind == "drag" and self.drag_object_id is not None:
            obj = self._object_by_id(self.drag_object_id)
            self.drag_object_id = None
            if math.hypot(obj.x-p["slot_x"], obj.y-p["slot_y"]) <= p["tolerance"]:
                obj.locked = True
                self._complete_stage({"drag_error_px": round(math.hypot(obj.x-p["slot_x"], obj.y-p["slot_y"]), 3)})
            else:
                self.metrics.drag_misses += 1
                self._fail("drag_drop_miss", "MOTOR", {})
            return
        if kind == "assembly" and self.drag_object_id is not None:
            obj = self._object_by_id(self.drag_object_id)
            self.drag_object_id = None
            slot = next(s for s in p["slots"] if s["piece_id"] == obj.object_id)
            if math.hypot(obj.x-slot["x"], obj.y-slot["y"]) <= p["tolerance"]:
                obj.x, obj.y, obj.locked = slot["x"], slot["y"], True
                self.assembly_locked.add(obj.object_id)
                self._event("assembly_lock", {"piece": obj.object_id, "count": len(self.assembly_locked)})
                if len(self.assembly_locked) == len(p["pieces"]):
                    self._complete_stage({"pieces": len(self.assembly_locked)})
            else:
                self.metrics.assembly_misses += 1
                self._fail("assembly_drop_miss", "MOTOR", {"piece": obj.object_id})
            return
        if kind == "trace" and self.trace_started:
            self.trace_started = False
            if self.trace_checkpoint == len(p["points"])-1:
                self._complete_stage({"checkpoints": len(p["points"])})
            else:
                self.metrics.trace_deviations += 1
                self._fail("trace_incomplete", "MOTOR", {"checkpoint": self.trace_checkpoint})

    def click(self, x: float, y: float) -> None:
        before = self.stage_index
        self.pointer_down(x, y)
        if not self.done and self.stage_index == before:
            self.pointer_up(x, y)

    def text_key(self, keysym: str, char: str) -> None:
        if self.done or self.stage.kind != "typing" or not self.terminal_focused:
            return
        self.metrics.actions += 1
        self.metrics.key_events += 1
        if keysym == "BackSpace":
            self.text_buffer = self.text_buffer[:-1]
            self._event("text_edit", {"op":"backspace", "length":len(self.text_buffer)})
            return
        if keysym in {"Return", "KP_Enter"}:
            expected = str(self.stage.payload["code"])
            if self.text_buffer == expected:
                self._complete_stage({"typing_length":len(expected)})
            else:
                self.metrics.typing_errors += 1
                self._fail("typing_error", "TYPING", {"typed_length":len(self.text_buffer), "expected_length":len(expected)})
            return
        if char and char in string.printable and char not in "\r\n\t\x0b\x0c":
            self.text_buffer += char.upper()
            self._event("text_edit", {"op":"append", "length":len(self.text_buffer)})

    def report(self) -> dict[str, Any]:
        cpu = peak_rss_kb = None
        try:
            import resource
            usage = resource.getrusage(resource.RUSAGE_SELF)
            cpu = usage.ru_utime + usage.ru_stime
            peak_rss_kb = usage.ru_maxrss
        except Exception:
            pass
        return {
            "schema": "procedural-control-arena-report-v1",
            "episode": self.spec.to_dict(include_seed=True),
            "fingerprint": self.spec.public_fingerprint(),
            "success": self.success,
            "failure_reason": self.failure_reason,
            "failure_locus": self.failure_locus,
            "sim_time": round(self.sim_time, 6),
            "wall_time": round(time.monotonic() - self.started_wall, 6),
            "process_cpu_seconds": None if cpu is None else round(cpu, 6),
            "peak_rss_kb": peak_rss_kb,
            "metrics": asdict(self.metrics),
            "stage_results": self.stage_results,
            "events": [asdict(e) for e in self.events],
        }


def solve_with_oracle_for_test(session: BenchmarkSession, *, tick: float = 1/TICK_HZ) -> None:
    """Positive-control helper for construction tests only; never expose to an evaluated controller."""
    guard = 0
    while not session.done and guard < 200_000:
        guard += 1
        stage, p = session.stage, session.stage.payload
        if stage.kind == "move":
            dx, dy = p["zone_x"]-session.player_x, p["zone_y"]-session.player_y
            desired: set[str] = set()
            if abs(dx) > 1: desired.add("d" if dx > 0 else "a")
            if abs(dy) > 1: desired.add("s" if dy > 0 else "w")
            for k in desired - session.keys_down: session.key_down(k)
            for k in set(session.keys_down) - desired: session.key_up(k)
            session.step(tick)
        elif stage.kind == "target":
            obj = session._object_by_id(p["target_id"]); session.click(obj.x, obj.y)
        elif stage.kind == "switch":
            while session.stage_elapsed < p["wait_seconds"] and not session.done: session.step(tick)
            if not session.done:
                obj = session._object_by_id(p["active_id"]); session.click(obj.x, obj.y)
        elif stage.kind == "typing":
            session.pointer_down(p["terminal_x"]+p["terminal_w"]/2, p["terminal_y"]+p["terminal_h"]/2)
            for ch in p["code"]: session.text_key(ch, ch)
            session.text_key("Return", "\r")
        elif stage.kind == "combo":
            key = p["required_key"]; session.key_down(key)
            obj = session._object_by_id(p["target_id"]); session.click(obj.x, obj.y)
            session.key_up(key)
        elif stage.kind == "drag":
            obj = session.objects[0]; session.pointer_down(obj.x, obj.y); session.pointer_move(p["slot_x"], p["slot_y"]); session.pointer_up(p["slot_x"], p["slot_y"])
        elif stage.kind == "assembly":
            for piece_spec in p["pieces"]:
                if session.done: break
                obj = session._object_by_id(piece_spec["object_id"])
                if obj.locked: continue
                slot = next(s for s in p["slots"] if s["piece_id"] == obj.object_id)
                session.pointer_down(obj.x, obj.y); session.pointer_move(slot["x"], slot["y"]); session.pointer_up(slot["x"], slot["y"])
        elif stage.kind == "trace":
            pts = p["points"]; session.pointer_down(*pts[0])
            for point in pts[1:]:
                if session.done: break
                session.pointer_move(*point)
            if not session.done: session.pointer_up(*pts[-1])
        elif stage.kind == "recovery":
            obj = session._object_by_id(p["target_id"]); session.click(obj.x, obj.y)
            if not session.done and session.stage.kind == "recovery":
                obj = session._object_by_id(p["target_id"]); session.click(obj.x, obj.y)
        else:
            raise RuntimeError(stage.kind)
    if guard >= 200_000 and not session.done:
        raise RuntimeError("oracle guard exceeded")
