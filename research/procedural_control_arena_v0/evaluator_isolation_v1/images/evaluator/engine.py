from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
import math
import random
import secrets
import string
import time
from typing import Any

WIDTH = 640
HEIGHT = 480
HUD_HEIGHT = 96
PLAY_TOP = HUD_HEIGHT
PLAY_BOTTOM = HEIGHT - 20
TICK_HZ = 60.0

COLORS = ("blue", "red", "green", "yellow", "purple", "orange")
SHAPES = ("circle", "square", "triangle", "diamond")


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
    move_zone_radius: float
    move_deadline: float
    target_deadline: float
    switch_wait: float
    switch_deadline: float
    typing_length: int
    typing_deadline: float

    @classmethod
    def from_level(cls, level: float) -> "DifficultyProfile":
        d = _clamp(float(level), 0.0, 1.0)
        return cls(
            level=d,
            target_radius=_lerp(34.0, 10.0, d),
            target_speed=_lerp(0.0, 165.0, d),
            distractor_count=int(round(_lerp(2.0, 10.0, d))),
            move_zone_radius=_lerp(70.0, 24.0, d),
            move_deadline=_lerp(10.0, 4.0, d),
            target_deadline=_lerp(8.0, 2.6, d),
            switch_wait=_lerp(2.4, 0.65, d),
            switch_deadline=_lerp(6.0, 2.2, d),
            typing_length=int(round(_lerp(3.0, 10.0, d))),
            typing_deadline=_lerp(10.0, 4.0, d),
        )


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
    difficulty: DifficultyProfile
    stages: tuple[StageSpec, ...]

    def public_fingerprint(self) -> str:
        # Fingerprint is useful for pairing/replay but does not expose the seed.
        payload = self.to_dict(include_seed=False)
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(raw).hexdigest()[:16]

    def to_dict(self, *, include_seed: bool) -> dict[str, Any]:
        data = {
            "schema": self.schema,
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


def _unique_semantics(rng: random.Random, count: int) -> list[tuple[str, str]]:
    pool = [(c, s) for c in COLORS for s in SHAPES]
    rng.shuffle(pool)
    if count > len(pool):
        raise ValueError("requested more unique visual semantics than available")
    return pool[:count]


def _target_payload(rng: random.Random, d: DifficultyProfile, *, switch: bool) -> dict[str, Any]:
    count = d.distractor_count + (2 if switch else 1)
    semantics = _unique_semantics(rng, count)
    objects: list[ObjectSpec] = []
    margin = d.target_radius + 8
    for idx, (color, shape) in enumerate(semantics):
        x = y = 0.0
        for _ in range(128):
            x, y = _safe_point(rng, margin)
            if all(math.hypot(x - other.x, y - other.y) >= d.target_radius * 2.4 for other in objects):
                break
        vx, vy = _velocity(rng, d.target_speed)
        objects.append(ObjectSpec(f"obj-{idx}", color, shape, x, y, vx, vy, d.target_radius))
    if switch:
        prepared_idx, active_idx = rng.sample(range(len(objects)), 2)
        return {
            "objects": [asdict(o) for o in objects],
            "prepared_id": objects[prepared_idx].object_id,
            "active_id": objects[active_idx].object_id,
            "wait_seconds": d.switch_wait,
            "deadline": d.switch_deadline,
        }
    target = rng.choice(objects)
    return {
        "objects": [asdict(o) for o in objects],
        "target_id": target.object_id,
        "deadline": d.target_deadline,
    }


def generate_episode(seed: int, difficulty: float) -> EpisodeSpec:
    rng = random.Random(int(seed))
    d = DifficultyProfile.from_level(difficulty)
    zone_x, zone_y = _safe_point(rng, d.move_zone_radius + 12)
    code_alphabet = string.ascii_uppercase + string.digits
    code = "".join(rng.choice(code_alphabet) for _ in range(d.typing_length))
    terminal_w = _lerp(190.0, 125.0, d.level)
    terminal_h = _lerp(68.0, 46.0, d.level)
    terminal_x = rng.uniform(20.0, WIDTH - terminal_w - 20.0)
    terminal_y = rng.uniform(PLAY_TOP + 30.0, PLAY_BOTTOM - terminal_h - 10.0)
    stages = [
        StageSpec("move", {
            "zone_x": zone_x,
            "zone_y": zone_y,
            "zone_radius": d.move_zone_radius,
            "deadline": d.move_deadline,
        }),
        StageSpec("target", _target_payload(rng, d, switch=False)),
        StageSpec("switch", _target_payload(rng, d, switch=True)),
        StageSpec("typing", {
            "code": code,
            "terminal_x": terminal_x,
            "terminal_y": terminal_y,
            "terminal_w": terminal_w,
            "terminal_h": terminal_h,
            "deadline": d.typing_deadline,
        }),
    ]
    rng.shuffle(stages)
    return EpisodeSpec("procedural-control-arena-v0", int(seed), d, tuple(stages))


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

    @classmethod
    def from_spec(cls, spec: dict[str, Any]) -> "RuntimeObject":
        return cls(**spec)

    def step(self, dt: float) -> None:
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


class BenchmarkSession:
    """State machine for the benchmark. Hidden oracle state stays inside this object."""

    def __init__(self, spec: EpisodeSpec):
        self.spec = spec
        self.started_wall = time.monotonic()
        self.sim_time = 0.0
        self.stage_started = 0.0
        self.stage_index = 0
        self.done = False
        self.success = False
        self.failure_reason: str | None = None
        self.events: list[SessionEvent] = []
        self.keys_down: set[str] = set()
        self.player_x = WIDTH / 2.0
        self.player_y = (PLAY_TOP + PLAY_BOTTOM) / 2.0
        self.player_speed = 180.0
        self.objects: list[RuntimeObject] = []
        self.terminal_focused = False
        self.text_buffer = ""
        self._load_stage()
        self._event("episode_start", {"fingerprint": spec.public_fingerprint()})

    @property
    def stage(self) -> StageSpec:
        return self.spec.stages[self.stage_index]

    @property
    def stage_elapsed(self) -> float:
        return self.sim_time - self.stage_started

    def _event(self, name: str, detail: dict[str, Any] | None = None) -> None:
        self.events.append(SessionEvent(
            round(self.sim_time, 6),
            round(time.monotonic() - self.started_wall, 6),
            self.stage_index,
            name,
            detail or {},
        ))

    def _load_stage(self) -> None:
        if self.stage_index >= len(self.spec.stages):
            self.done = True
            self.success = True
            return
        self.stage_started = self.sim_time
        self.keys_down.clear()
        self.terminal_focused = False
        self.text_buffer = ""
        payload = self.stage.payload
        self.objects = [RuntimeObject.from_spec(o) for o in payload.get("objects", [])]
        self._event("stage_start", {"kind": self.stage.kind})

    def _complete_stage(self, detail: dict[str, Any] | None = None) -> None:
        if self.done:
            return
        self._event("stage_success", detail or {})
        self.stage_index += 1
        if self.stage_index >= len(self.spec.stages):
            self.done = True
            self.success = True
            self.keys_down.clear()
            self._event("episode_success", {})
            return
        self._load_stage()

    def _fail(self, reason: str, detail: dict[str, Any] | None = None) -> None:
        if self.done:
            return
        self.failure_reason = reason
        self.done = True
        self.success = False
        self.keys_down.clear()
        self._event("episode_failure", {"reason": reason, **(detail or {})})

    def deadline(self) -> float:
        return float(self.stage.payload["deadline"])

    def instruction(self) -> str:
        if self.done:
            return "SUCCESS" if self.success else f"FAILED: {self.failure_reason}"
        p = self.stage.payload
        if self.stage.kind == "move":
            return "MOVE: use WASD to enter the striped goal zone."
        if self.stage.kind == "target":
            target = self._object_by_id(p["target_id"])
            return f"TARGET: click the {target.color} {target.shape}."
        if self.stage.kind == "switch":
            prepared = self._object_by_id(p["prepared_id"])
            active = self._object_by_id(p["active_id"])
            if self.stage_elapsed < float(p["wait_seconds"]):
                return f"WAIT: do not click. Prepare for the {prepared.color} {prepared.shape}."
            return f"GO / SWITCH: ignore the prepared target; click the {active.color} {active.shape}."
        if self.stage.kind == "typing":
            return f"TYPE: click the terminal, type {p['code']}, then press Enter."
        raise RuntimeError(f"unknown stage {self.stage.kind}")

    def public_state(self) -> dict[str, Any]:
        # Deliberately excludes seed, correct object IDs, and future stage payloads.
        state = {
            "schema": "procedural-control-arena-public-v0",
            "fingerprint": self.spec.public_fingerprint(),
            "sim_time": round(self.sim_time, 6),
            "stage_index": self.stage_index,
            "stage_count": len(self.spec.stages),
            "instruction": self.instruction(),
            "done": self.done,
            "success": self.success if self.done else None,
        }
        return state

    def _object_by_id(self, object_id: str) -> RuntimeObject:
        for obj in self.objects:
            if obj.object_id == object_id:
                return obj
        raise KeyError(object_id)

    @staticmethod
    def _contains(obj: RuntimeObject, x: float, y: float) -> bool:
        dx = x - obj.x
        dy = y - obj.y
        r = obj.radius
        if obj.shape == "circle":
            return dx * dx + dy * dy <= r * r
        if obj.shape == "square":
            return abs(dx) <= r and abs(dy) <= r
        if obj.shape == "diamond":
            return abs(dx) + abs(dy) <= r
        if obj.shape == "triangle":
            # Rendered triangle vertices: (0,-r), (-r,r), (r,r).
            return -r <= dy <= r and abs(dx) <= (dy + r) / 2.0
        return False

    def _object_at(self, x: float, y: float) -> RuntimeObject | None:
        # Smallest center-distance wins only in the rare case of overlap.
        candidates = []
        for obj in self.objects:
            dist = math.hypot(obj.x - x, obj.y - y)
            if self._contains(obj, x, y):
                candidates.append((dist, obj))
        if not candidates:
            return None
        candidates.sort(key=lambda pair: pair[0])
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
            if math.hypot(self.player_x - p["zone_x"], self.player_y - p["zone_y"]) <= p["zone_radius"]:
                self._complete_stage({"motor": "move"})
                return
        if self.stage_elapsed > self.deadline():
            self._fail("deadline_miss", {"stage": self.stage.kind})

    def key_down(self, key: str) -> None:
        if self.done:
            return
        key = key.lower()
        if key in {"w", "a", "s", "d"}:
            self.keys_down.add(key)
            self._event("key_down", {"key": key})

    def key_up(self, key: str) -> None:
        key = key.lower()
        if key in self.keys_down:
            self.keys_down.remove(key)
            self._event("key_up", {"key": key})

    def click(self, x: float, y: float) -> None:
        if self.done:
            return
        self._event("click", {"x": round(x, 2), "y": round(y, 2)})
        p = self.stage.payload
        if self.stage.kind == "target":
            hit = self._object_at(x, y)
            if hit is None:
                self._fail("motor_miss", {"stage": "target"})
            elif hit.object_id == p["target_id"]:
                self._complete_stage({"motor": "pointer", "semantic": f"{hit.color}:{hit.shape}"})
            else:
                self._fail("wrong_target", {"semantic": f"{hit.color}:{hit.shape}"})
            return
        if self.stage.kind == "switch":
            hit = self._object_at(x, y)
            if self.stage_elapsed < float(p["wait_seconds"]):
                self._fail("premature_action", {"hit": None if hit is None else f"{hit.color}:{hit.shape}"})
                return
            if hit is None:
                self._fail("motor_miss", {"stage": "switch"})
            elif hit.object_id == p["active_id"]:
                self._complete_stage({"freshness": "switch_accepted"})
            elif hit.object_id == p["prepared_id"]:
                self._fail("stale_action", {"semantic": f"{hit.color}:{hit.shape}"})
            else:
                self._fail("wrong_target", {"semantic": f"{hit.color}:{hit.shape}"})
            return
        if self.stage.kind == "typing":
            tx, ty = p["terminal_x"], p["terminal_y"]
            tw, th = p["terminal_w"], p["terminal_h"]
            if tx <= x <= tx + tw and ty <= y <= ty + th:
                self.terminal_focused = True
                self._event("terminal_focus", {})
            else:
                self.terminal_focused = False
            return
        self._event("irrelevant_click", {"stage": self.stage.kind})

    def text_key(self, keysym: str, char: str) -> None:
        if self.done or self.stage.kind != "typing" or not self.terminal_focused:
            return
        if keysym == "BackSpace":
            self.text_buffer = self.text_buffer[:-1]
            self._event("text_edit", {"op": "backspace", "length": len(self.text_buffer)})
            return
        if keysym in {"Return", "KP_Enter"}:
            expected = str(self.stage.payload["code"])
            if self.text_buffer == expected:
                self._complete_stage({"typing_length": len(expected)})
            else:
                self._fail("typing_error", {"typed_length": len(self.text_buffer), "expected_length": len(expected)})
            return
        if char and char in string.printable and char not in "\r\n\t\x0b\x0c":
            self.text_buffer += char.upper()
            self._event("text_edit", {"op": "append", "length": len(self.text_buffer)})

    def report(self) -> dict[str, Any]:
        cpu = None
        peak_rss_kb = None
        try:
            import resource
            usage = resource.getrusage(resource.RUSAGE_SELF)
            cpu = usage.ru_utime + usage.ru_stime
            peak_rss_kb = usage.ru_maxrss
        except Exception:
            pass
        return {
            "schema": "procedural-control-arena-report-v0",
            "episode": self.spec.to_dict(include_seed=True),
            "fingerprint": self.spec.public_fingerprint(),
            "success": self.success,
            "failure_reason": self.failure_reason,
            "sim_time": round(self.sim_time, 6),
            "wall_time": round(time.monotonic() - self.started_wall, 6),
            "process_cpu_seconds": None if cpu is None else round(cpu, 6),
            "peak_rss_kb": peak_rss_kb,
            "events": [asdict(e) for e in self.events],
        }


def solve_with_oracle_for_test(session: BenchmarkSession, *, tick: float = 1 / TICK_HZ) -> None:
    """Positive-control helper for self-tests only. Never expose this to an evaluated agent."""
    guard = 0
    while not session.done and guard < 100_000:
        guard += 1
        stage = session.stage
        p = stage.payload
        if stage.kind == "move":
            dx = p["zone_x"] - session.player_x
            dy = p["zone_y"] - session.player_y
            session.keys_down.clear()
            if abs(dx) > 1:
                session.keys_down.add("d" if dx > 0 else "a")
            if abs(dy) > 1:
                session.keys_down.add("s" if dy > 0 else "w")
            session.step(tick)
        elif stage.kind == "target":
            obj = session._object_by_id(p["target_id"])
            session.click(obj.x, obj.y)
        elif stage.kind == "switch":
            while session.stage_elapsed < p["wait_seconds"] and not session.done:
                session.step(tick)
            if not session.done:
                obj = session._object_by_id(p["active_id"])
                session.click(obj.x, obj.y)
        elif stage.kind == "typing":
            tx = p["terminal_x"] + p["terminal_w"] / 2
            ty = p["terminal_y"] + p["terminal_h"] / 2
            session.click(tx, ty)
            for ch in p["code"]:
                session.text_key(ch, ch)
            session.text_key("Return", "\r")
        else:
            raise RuntimeError(stage.kind)
    if guard >= 100_000:
        raise RuntimeError("positive-control solver guard exhausted")
