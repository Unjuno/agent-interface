"""Formal MAP01 bounded-recovery mechanism v6 runner.

V6 preserves the v4/v5 scientific condition. It inherits v5's non-destructive
session event waiting and changes only the planner-window boundary: planner end is
sampled immediately after the fixed-delay provider returns, before fallback
cancellation/release cleanup or any optional release wait.
"""
from __future__ import annotations
import json
import queue
import threading

ALLOCATION_ID = "map01-recovery-cover-mechanism-live-v6-01"
WORKFLOW_PATH = ".github/workflows/map01-recovery-cover-mechanism-live-v6-01.yml"


def configure():
    import map01_recovery_cover_mechanism_v5_runner as v5
    base = v5.configure()
    base.ALLOCATION_ID = ALLOCATION_ID
    base.EXPECTED_WORKFLOW_PATH = WORKFLOW_PATH

    def _run_arm(root, pair_index, arm, fixture):
        arm_root = root / f"pair-{pair_index:02d}" / arm.lower()
        runtime = arm_root / "runtime"
        arm_root.mkdir(parents=True, exist_ok=False)
        session = base.JsonSession(base._session_command(runtime, fixture))
        fallback_id = f"pair{pair_index}-{arm.lower()}-fallback"
        try:
            session.wait(lambda r: r.get("event") == "ready", timeout=25)
            session.wait(lambda r: r.get("event") == "observation", timeout=15)

            prelude_seq = session.latest_exact["sequence"]
            now = session.runtime_clock()
            base._submit(
                session,
                f"pair{pair_index}-{arm.lower()}-prelude",
                [{"op": "hold", "keys": list(base.PRELUDE_KEYS), "duration_ms": base.PRELUDE_MS}, {"op": "observe"}],
                now + 2_000_000_000,
            )
            session.wait(lambda r: r.get("event") == "terminal" and r.get("id", "").endswith("-prelude"), timeout=10)
            base._wait_exact_after(session, prelude_seq)
            source_exact, source_typed, source_health = base._source_guard(session)

            planner_start_ns = session.runtime_clock()
            timer_done = threading.Event()
            timer = threading.Timer(base.PLANNER_WAIT_MS / 1000.0, timer_done.set)
            timer.start()
            guard_cancel_reason = None
            fallback_terminal = None

            if arm == "COAST_CONTROL":
                base._submit(session, fallback_id, base.build_coast_steps(), planner_start_ns + (base.PLANNER_WAIT_MS + 1000) * 1_000_000)
            elif arm == "BOUNDED_RECOVERY":
                valid_until = base.recovery_valid_until_ns(source_exact["capture_ns"], planner_start_ns)
                base._submit(session, fallback_id, base.build_recovery_steps(), valid_until)
            else:
                raise ValueError(f"unknown arm: {arm}")

            while not timer_done.is_set():
                try:
                    row = session.queue.get(timeout=0.02)
                except queue.Empty:
                    if session.process.poll() is not None:
                        raise base.SessionError("session exited during planner wait")
                    continue
                if row.get("event") == "terminal" and row.get("id") == fallback_id:
                    fallback_terminal = row
                if arm == "BOUNDED_RECOVERY" and guard_cancel_reason is None and row.get("event") == "typed_observation":
                    failed, reason = base.recovery_guard_failed(source_health, source_exact["sequence"], row)
                    if failed:
                        guard_cancel_reason = reason
                        session.send({"op": "cancel", "id": fallback_id})

            planner_end_ns = session.runtime_clock()
            timer.cancel()

            if fallback_terminal is None:
                session.send({"op": "cancel", "id": fallback_id})
                session.wait(lambda r: r.get("event") == "cancel_requested" and r.get("id") == fallback_id)
                try:
                    session.wait(lambda r: r.get("event") in {"input_released", "input_release_unverified"} and r.get("id") == fallback_id, timeout=3)
                except TimeoutError:
                    pass
                fallback_terminal = session.wait(lambda r: r.get("event") == "terminal" and r.get("id") == fallback_id, timeout=5)

            window = base.Window(planner_start_ns, planner_end_ns)
            session.send({"op": "finish"})
            session.wait(lambda r: r.get("event") == "post_control_score", timeout=10)
            session.process.wait(timeout=15)

            events = list(session.events)
            bounds = base.fallback_input_bounds(events, fallback_id, window)
            release_ok = base.terminal_release_ok(events, fallback_id)
            score = base.load_json(runtime / "score.json")
            scorer_summary = base.load_json(runtime / "scorer-summary.json")
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
                "planner_window": {
                    "start_ns": planner_start_ns,
                    "end_ns": planner_end_ns,
                    "duration_ns": window.duration_ns,
                    "end_boundary_phase": "immediately_after_delay_before_fallback_cleanup"
                },
                "fallback_id": fallback_id,
                "fallback_terminal_status": fallback_terminal.get("status"),
                "guard_cancel_reason": guard_cancel_reason,
                "terminal_release_verified": release_ok,
                "input_bounds": bounds,
                "scorer_summary": scorer_summary,
                "scorer_events": scorer_events,
                "score": score
            }
            (arm_root / "arm-summary.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            return result
        finally:
            session.terminate()

    base._run_arm = _run_arm
    return base


def main() -> None:
    configure().main()


if __name__ == "__main__":
    main()
