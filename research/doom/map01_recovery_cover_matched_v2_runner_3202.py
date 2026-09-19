from __future__ import annotations

import argparse
import json
import queue
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

HERE = Path(__file__).resolve().parent
ALLOCATION_ID = "map01-recovery-cover-matched-live-v2-02"
EXPECTED_OWNER_SCHEMA = "formal-allocation-global-owner-v1"
EXPECTED_WORKFLOW_PATH = ".github/workflows/map01-recovery-cover-matched-live-v2-02.yml"
FIXTURE_REL = Path("fixtures/map01-threat-contact-v2/fixture.json")
FORMAL_SEED = 990619
PLANNER_WAIT_MS = 600
PRELUDE_KEYS = ("d",)
PRELUDE_MS = 180
RECOVERY_KEYS = PRELUDE_KEYS
RECOVERY_PULSE_MS = 50
RECOVERY_PULSES = 5
RECOVERY_LEASE_MS = 400
SOURCE_MAX_AGE_MS = 1000
COAST_SAMPLE_MS = 50
PAIR_ORDER = (
    ("COAST_CONTROL", "BOUNDED_RECOVERY"),
    ("BOUNDED_RECOVERY", "COAST_CONTROL"),
    ("COAST_CONTROL", "BOUNDED_RECOVERY"),
)


@dataclass(frozen=True)
class Window:
    start_ns: int
    end_ns: int

    def __post_init__(self) -> None:
        if type(self.start_ns) is not int or type(self.end_ns) is not int:
            raise TypeError("window endpoints must be int")
        if self.end_ns <= self.start_ns:
            raise ValueError("window must be positive")

    @property
    def duration_ns(self) -> int:
        return self.end_ns - self.start_ns


class SessionError(RuntimeError):
    pass


def load_json(path: Path) -> dict:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def validate_launch_owner(receipt: dict) -> None:
    required = {
        "schema": EXPECTED_OWNER_SCHEMA,
        "allocation_id": ALLOCATION_ID,
        "workflow_path": EXPECTED_WORKFLOW_PATH,
        "required_branch": "main",
        "result_class": "PASS_CANONICAL_GLOBAL_OWNER",
        "may_enter_formal_step": True,
        "current_head_branch": "main",
        "owner_head_branch": "main",
        "matching_run_count": 1,
    }
    for key, expected in required.items():
        if receipt.get(key) != expected:
            raise ValueError(f"launch owner mismatch {key}: {receipt.get(key)!r} != {expected!r}")
    if receipt.get("current_run_id") != receipt.get("owner_run_id"):
        raise ValueError("current run is not canonical owner")


def build_coast_steps(wait_ms: int = PLANNER_WAIT_MS) -> list[dict]:
    if type(wait_ms) is not int or not 50 <= wait_ms <= 5000:
        raise ValueError("coast wait must be 50-5000 ms")
    return [{"op": "coast", "duration_ms": wait_ms, "sample_ms": COAST_SAMPLE_MS}]


def build_recovery_steps(
    keys: tuple[str, ...] = RECOVERY_KEYS,
    pulse_ms: int = RECOVERY_PULSE_MS,
    pulses: int = RECOVERY_PULSES,
) -> list[dict]:
    if not keys or len(keys) > 4 or any(not isinstance(key, str) or not key for key in keys):
        raise ValueError("recovery keys must contain 1-4 names")
    if type(pulse_ms) is not int or not 1 <= pulse_ms <= 5000:
        raise ValueError("invalid pulse_ms")
    if type(pulses) is not int or not 1 <= pulses <= 8:
        raise ValueError("invalid pulse count")
    steps: list[dict] = []
    for _ in range(pulses):
        steps.append({"op": "hold", "keys": list(keys), "duration_ms": pulse_ms})
        steps.append({"op": "observe"})
    if len(steps) > 16:
        raise AssertionError("recovery exceeds executor step limit")
    if pulse_ms * pulses > RECOVERY_LEASE_MS:
        raise AssertionError("hold time exceeds recovery lease")
    return steps


def recovery_valid_until_ns(source_capture_ns: int, runtime_now_ns: int) -> int:
    if any(type(v) is not int for v in (source_capture_ns, runtime_now_ns)):
        raise TypeError("timestamps must be int")
    deadline = min(
        runtime_now_ns + RECOVERY_LEASE_MS * 1_000_000,
        source_capture_ns + SOURCE_MAX_AGE_MS * 1_000_000,
    )
    if deadline <= runtime_now_ns:
        raise ValueError("source observation is stale before recovery admission")
    return deadline


def observed_health(typed: dict) -> int:
    if typed.get("event") != "typed_observation":
        raise ValueError("typed observation required")
    health = typed.get("signals", {}).get("health")
    if not isinstance(health, dict) or health.get("status") != "observed":
        raise ValueError("health is not independently observable to controller")
    value = health.get("value")
    if type(value) is not int or value < 0:
        raise ValueError("invalid health value")
    return value


def recovery_guard_failed(source_health: int, source_sequence: int, typed: dict) -> tuple[bool, str | None]:
    if type(source_health) is not int or type(source_sequence) is not int:
        raise TypeError("source guard must be concrete")
    if typed.get("event") != "typed_observation":
        return True, "non_typed_guard_event"
    seq = typed.get("sequence")
    if type(seq) is not int or seq <= source_sequence:
        return True, "non_fresh_sequence"
    try:
        health = observed_health(typed)
    except ValueError:
        return True, "health_unavailable"
    if health < source_health:
        return True, "health_loss"
    return False, None


def _clip(interval: tuple[int, int], window: Window) -> tuple[int, int] | None:
    lo = max(interval[0], window.start_ns)
    hi = min(interval[1], window.end_ns)
    return (lo, hi) if hi > lo else None


def union_duration_ns(intervals: Iterable[tuple[int, int]], window: Window) -> int:
    clipped = sorted(x for i in intervals if (x := _clip(i, window)) is not None)
    if not clipped:
        return 0
    total = 0
    lo, hi = clipped[0]
    for a, b in clipped[1:]:
        if a <= hi:
            hi = max(hi, b)
        else:
            total += hi - lo
            lo, hi = a, b
    return total + hi - lo


def fallback_input_bounds(events: list[dict], identifier: str, planner_window: Window) -> dict:
    accepted = [r for r in events if r.get("event") == "accepted" and r.get("id") == identifier]
    if len(accepted) != 1:
        raise ValueError(f"expected one accepted fallback {identifier}, got {len(accepted)}")
    token = accepted[0].get("intent_token")
    if not isinstance(token, str) or not token:
        raise ValueError("fallback accepted row lacks intent token")
    admissions: dict[str, list[dict]] = {}
    releases: dict[str, list[dict]] = {}
    for row in events:
        if row.get("intent_token") != token:
            continue
        if row.get("event") == "input_admission" and isinstance(row.get("key"), str):
            admissions.setdefault(row["key"], []).append(row)
        elif row.get("event") == "input_release_transition" and row.get("operation") == "up":
            releases.setdefault(row.get("key"), []).append(row)
    lower_intervals: list[tuple[int, int]] = []
    upper_intervals: list[tuple[int, int]] = []
    invalid: list[str] = []
    for key, starts in admissions.items():
        ends = releases.get(key, [])
        if len(starts) != len(ends):
            invalid.append(f"{key}:admission_release_count")
            continue
        for start, end in zip(starts, ends):
            if end.get("owner_transition_verified") is not True:
                invalid.append(f"{key}:unverified_release")
                continue
            fields = (
                start.get("admitted_ns"), start.get("input_ack_ns"),
                end.get("release_call_started_ns"), end.get("release_call_returned_ns"),
            )
            if any(type(x) is not int for x in fields):
                invalid.append(f"{key}:missing_clock")
                continue
            admitted, ack, release_start, release_return = fields
            if not admitted <= ack <= release_start <= release_return:
                invalid.append(f"{key}:clock_order")
                continue
            lower_intervals.append((ack, release_start))
            upper_intervals.append((admitted, release_return))
    if set(releases) - set(admissions):
        invalid.append("release_without_admission")
    lower = union_duration_ns(lower_intervals, planner_window)
    upper = union_duration_ns(upper_intervals, planner_window)
    if upper < lower or upper > planner_window.duration_ns:
        invalid.append("coverage_bounds")
    return {
        "intent_token": token,
        "valid": not invalid,
        "invalid": invalid,
        "planner_wait_ns": planner_window.duration_ns,
        "retained_input_lower_bound_ns": lower,
        "retained_input_upper_bound_ns": upper,
        "no_retained_input_lower_bound_ns": planner_window.duration_ns - upper,
        "no_retained_input_upper_bound_ns": planner_window.duration_ns - lower,
        "admission_count": sum(len(v) for v in admissions.values()),
        "release_count": sum(len(v) for v in releases.values()),
    }


def terminal_release_ok(events: list[dict], identifier: str) -> bool:
    rows = [r for r in events if r.get("event") == "terminal" and r.get("id") == identifier]
    if len(rows) != 1:
        return False
    release = rows[0].get("release")
    return isinstance(release, dict) and release.get("verified") is True


class JsonSession:
    def __init__(self, command: list[str]):
        self.process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self.queue: queue.Queue[dict] = queue.Queue()
        self.events: list[dict] = []
        self.latest_exact: dict | None = None
        self.latest_typed_by_sequence: dict[int, dict] = {}
        self._reader = threading.Thread(target=self._read, daemon=True)
        self._reader.start()

    def _read(self) -> None:
        assert self.process.stdout is not None
        for line in self.process.stdout:
            row = json.loads(line)
            self.events.append(row)
            if row.get("event") == "observation":
                self.latest_exact = row
            elif row.get("event") == "typed_observation" and type(row.get("sequence")) is int:
                self.latest_typed_by_sequence[row["sequence"]] = row
            self.queue.put(row)

    def send(self, command: dict) -> None:
        if self.process.poll() is not None:
            raise SessionError("session already exited")
        assert self.process.stdin is not None
        self.process.stdin.write(json.dumps(command, separators=(",", ":")) + "\n")
        self.process.stdin.flush()

    def wait(self, predicate, timeout: float = 20.0) -> dict:
        # A consumer may have observed an event at the planner-timer boundary
        # before a later cleanup wait asks for the same terminal event. Reuse
        # the immutable event log before blocking on the queue; this preserves
        # the first terminal outcome instead of turning it into a false
        # FAIL_SESSION_EVENT_TIMEOUT.
        for row in self.events:
            if predicate(row):
                return row
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                row = self.queue.get(timeout=min(0.1, max(0.01, deadline - time.monotonic())))
            except queue.Empty:
                if self.process.poll() is not None:
                    assert self.process.stderr is not None
                    raise SessionError(self.process.stderr.read().strip() or "session exited")
                continue
            if predicate(row):
                return row
        raise TimeoutError("session event timeout")

    def runtime_clock(self) -> int:
        self.send({"op": "clock"})
        row = self.wait(lambda r: r.get("event") == "clock")
        value = row.get("runtime_ns")
        if type(value) is not int:
            raise SessionError("runtime clock missing")
        return value

    def terminate(self) -> None:
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=3)


def _session_command(out: Path, fixture: Path) -> list[str]:
    return [
        sys.executable,
        str(HERE / "session_map01_v13.py"),
        "--out", str(out),
        "--seed", str(FORMAL_SEED),
        "--timeout-seconds", "60",
        "--skill", "1",
        "--load-fixture-manifest", str(fixture),
    ]


def _submit(session: JsonSession, identifier: str, steps: list[dict], valid_until_ns: int) -> dict:
    latest = session.latest_exact
    if not isinstance(latest, dict) or type(latest.get("sequence")) is not int:
        raise SessionError("exact observation required before submit")
    session.send({
        "op": "submit",
        "id": identifier,
        "expected_sequence": latest["sequence"],
        "valid_until_ns": valid_until_ns,
        "steps": steps,
    })
    row = session.wait(lambda r: r.get("event") in {"accepted", "rejected"})
    if row.get("event") != "accepted" or row.get("id") != identifier:
        raise SessionError(f"program rejected: {row}")
    return row


def _wait_exact_after(session: JsonSession, sequence: int, timeout: float = 10.0) -> dict:
    if session.latest_exact and session.latest_exact.get("sequence", -1) > sequence:
        return session.latest_exact
    return session.wait(lambda r: r.get("event") == "observation" and r.get("sequence", -1) > sequence, timeout)


def _source_guard(session: JsonSession) -> tuple[dict, dict, int]:
    exact = session.latest_exact
    if not isinstance(exact, dict):
        raise SessionError("missing exact source observation")
    seq = exact.get("sequence")
    if type(seq) is not int:
        raise SessionError("missing source sequence")
    typed = session.latest_typed_by_sequence.get(seq)
    if typed is None:
        typed = session.wait(lambda r: r.get("event") == "typed_observation" and r.get("sequence") == seq)
    return exact, typed, observed_health(typed)


def _run_arm(root: Path, pair_index: int, arm: str, fixture: Path) -> dict:
    arm_root = root / f"pair-{pair_index:02d}" / arm.lower()
    runtime = arm_root / "runtime"
    arm_root.mkdir(parents=True, exist_ok=False)
    session = JsonSession(_session_command(runtime, fixture))
    fallback_id = f"pair{pair_index}-{arm.lower()}-fallback"
    try:
        session.wait(lambda r: r.get("event") == "ready", timeout=25)
        session.wait(lambda r: r.get("event") == "observation", timeout=15)

        prelude_seq = session.latest_exact["sequence"]  # type: ignore[index]
        now = session.runtime_clock()
        _submit(
            session,
            f"pair{pair_index}-{arm.lower()}-prelude",
            [{"op": "hold", "keys": list(PRELUDE_KEYS), "duration_ms": PRELUDE_MS}, {"op": "observe"}],
            now + 2_000_000_000,
        )
        session.wait(lambda r: r.get("event") == "terminal" and r.get("id", "").endswith("-prelude"), timeout=10)
        _wait_exact_after(session, prelude_seq)
        source_exact, source_typed, source_health = _source_guard(session)

        planner_start_ns = session.runtime_clock()
        timer_done = threading.Event()
        timer = threading.Timer(PLANNER_WAIT_MS / 1000.0, timer_done.set)
        timer.start()
        guard_cancel_reason = None
        fallback_terminal = None

        if arm == "COAST_CONTROL":
            _submit(
                session,
                fallback_id,
                build_coast_steps(),
                planner_start_ns + (PLANNER_WAIT_MS + 1000) * 1_000_000,
            )
        elif arm == "BOUNDED_RECOVERY":
            valid_until = recovery_valid_until_ns(source_exact["capture_ns"], planner_start_ns)
            _submit(session, fallback_id, build_recovery_steps(), valid_until)
        else:
            raise ValueError(f"unknown arm: {arm}")

        while not timer_done.is_set():
            try:
                row = session.queue.get(timeout=0.02)
            except queue.Empty:
                if session.process.poll() is not None:
                    raise SessionError("session exited during planner wait")
                continue
            if row.get("event") == "terminal" and row.get("id") == fallback_id:
                fallback_terminal = row
            if arm == "BOUNDED_RECOVERY" and guard_cancel_reason is None and row.get("event") == "typed_observation":
                failed, reason = recovery_guard_failed(source_health, source_exact["sequence"], row)
                if failed:
                    guard_cancel_reason = reason
                    session.send({"op": "cancel", "id": fallback_id})

        timer.cancel()
        if fallback_terminal is None:
            session.send({"op": "cancel", "id": fallback_id})
            session.wait(lambda r: r.get("event") == "cancel_requested" and r.get("id") == fallback_id)
            try:
                session.wait(lambda r: r.get("event") in {"input_released", "input_release_unverified"} and r.get("id") == fallback_id, timeout=3)
            except TimeoutError:
                pass
            fallback_terminal = session.wait(lambda r: r.get("event") == "terminal" and r.get("id") == fallback_id, timeout=5)

        planner_end_ns = session.runtime_clock()
        window = Window(planner_start_ns, planner_end_ns)
        session.send({"op": "finish"})
        session.wait(lambda r: r.get("event") == "post_control_score", timeout=10)
        session.process.wait(timeout=15)

        events = list(session.events)
        bounds = fallback_input_bounds(events, fallback_id, window)
        release_ok = terminal_release_ok(events, fallback_id)
        score = load_json(runtime / "score.json")
        scorer_summary = load_json(runtime / "scorer-summary.json")
        scorer_events_path = runtime / "scorer-events.jsonl"
        scorer_events = []
        if scorer_events_path.exists():
            scorer_events = [json.loads(line) for line in scorer_events_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        result = {
            "arm": arm,
            "pair_index": pair_index,
            "source_sequence": source_exact["sequence"],
            "source_capture_ns": source_exact["capture_ns"],
            "source_health": source_health,
            "source_typed_frame_sha256": source_typed.get("frame_rgb_sha256"),
            "planner_window": {"start_ns": planner_start_ns, "end_ns": planner_end_ns, "duration_ns": window.duration_ns},
            "fallback_id": fallback_id,
            "fallback_terminal_status": fallback_terminal.get("status"),
            "guard_cancel_reason": guard_cancel_reason,
            "terminal_release_verified": release_ok,
            "input_bounds": bounds,
            "scorer_summary": scorer_summary,
            "scorer_events": scorer_events,
            "score": score,
        }
        (arm_root / "arm-summary.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return result
    finally:
        session.terminate()


def classify_pair(coast: dict, recovery: dict) -> dict:
    failures = []
    for row in (coast, recovery):
        if row.get("terminal_release_verified") is not True:
            failures.append(f"{row.get('arm')}:terminal_release")
        bounds = row.get("input_bounds", {})
        if bounds.get("valid") is not True:
            failures.append(f"{row.get('arm')}:input_bounds")
        scheduler = row.get("scorer_summary", {}).get("scheduler", {})
        if scheduler.get("missed_sample_periods") != 0:
            failures.append(f"{row.get('arm')}:scorer_missed_period")
    c = coast["input_bounds"]["no_retained_input_upper_bound_ns"]
    rr = recovery["input_bounds"]["no_retained_input_upper_bound_ns"]
    positive = [e for e in recovery.get("scorer_events", []) if e.get("useful") is True]
    negative = [e for e in recovery.get("scorer_events", []) if e.get("polarity") == "negative"]
    score_fields = ("kill_count", "death_count", "map_exit", "player_dead", "episode_finished")
    score_delta = {k: [coast["score"].get(k), recovery["score"].get(k)] for k in score_fields}
    return {
        "failures": failures,
        "coast_no_retained_input_upper_ns": c,
        "recovery_no_retained_input_upper_ns": rr,
        "recovery_minus_coast_no_input_upper_ns": rr - c,
        "continuity_improved": rr < c,
        "recovery_positive_event_count": len(positive),
        "recovery_negative_event_count": len(negative),
        "terminal_score_fields_coast_recovery": score_delta,
    }


def classify_all(arms: list[dict]) -> dict:
    pairs = []
    by_pair: dict[int, dict[str, dict]] = {}
    for arm in arms:
        by_pair.setdefault(arm["pair_index"], {})[arm["arm"]] = arm
    for index in sorted(by_pair):
        pair = by_pair[index]
        if set(pair) != {"COAST_CONTROL", "BOUNDED_RECOVERY"}:
            raise ValueError(f"incomplete pair {index}")
        pairs.append({"pair_index": index, **classify_pair(pair["COAST_CONTROL"], pair["BOUNDED_RECOVERY"])})
    hard_failures = [f"pair{p['pair_index']}:{x}" for p in pairs for x in p["failures"]]
    improved = [p for p in pairs if p["continuity_improved"]]
    useful = [p for p in pairs if p["recovery_positive_event_count"] > 0]
    harmful = [p for p in pairs if p["recovery_negative_event_count"] > 0]
    if hard_failures:
        decision = "FAIL"
    elif not improved:
        decision = "HOLD"
    elif harmful and not useful:
        decision = "FAIL"
    elif useful:
        decision = "PASS_CANDIDATE_REQUIRES_TERMINAL_AUDIT"
    else:
        decision = "HOLD_MECHANISM_ONLY"
    return {"schema": "map01-recovery-cover-matched-v2-runner-summary", "decision": decision, "hard_failures": hard_failures, "pairs": pairs}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--launch-owner", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, default=HERE / FIXTURE_REL)
    args = parser.parse_args()
    validate_launch_owner(load_json(args.launch_owner))
    if args.out.exists():
        raise ValueError("output path must not exist")
    args.out.mkdir(parents=True)
    fixture = args.fixture.resolve()
    fixture_data = load_json(fixture)
    if fixture_data.get("fixture_id") != "map01-threat-contact-v2" or fixture_data.get("seed") != FORMAL_SEED:
        raise ValueError("unexpected matched fixture")
    construction = {
        "allocation_id": ALLOCATION_ID,
        "model_calls": 0,
        "planner_provider": "frozen-delay-provider-v1",
        "planner_wait_ms": PLANNER_WAIT_MS,
        "prelude": {"keys": list(PRELUDE_KEYS), "duration_ms": PRELUDE_MS},
        "recovery": {"keys": list(RECOVERY_KEYS), "pulse_ms": RECOVERY_PULSE_MS, "pulses": RECOVERY_PULSES, "lease_ms": RECOVERY_LEASE_MS, "source_max_age_ms": SOURCE_MAX_AGE_MS},
        "pair_order": PAIR_ORDER,
        "fixture": str(fixture),
        "claim_scope": "real MAP01 mechanism/effect block; zero model calls; not frontier-model efficacy",
    }
    (args.out / "construction.json").write_text(json.dumps(construction, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    arms = []
    for pair_index, order in enumerate(PAIR_ORDER, start=1):
        for arm in order:
            arms.append(_run_arm(args.out, pair_index, arm, fixture))
    summary = classify_all(arms)
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"decision": summary["decision"], "pairs": len(summary["pairs"])}))


if __name__ == "__main__":
    main()
