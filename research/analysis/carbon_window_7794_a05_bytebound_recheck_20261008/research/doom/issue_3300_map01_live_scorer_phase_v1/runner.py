from __future__ import annotations

import argparse
import hashlib
import json
import os
import threading
import time
import traceback
from pathlib import Path

import vizdoom as vd
from session_map01_v13 import _coherent_progress_sample

HERE = Path(__file__).resolve().parent
SCHEDULE = json.loads((HERE / "schedule.json").read_text(encoding="utf-8"))
GETTERS = {
    "get_episode_time",
    "is_episode_finished",
    "is_player_dead",
    "get_game_variable",
    "get_ticrate",
    "is_episode_timeout_reached",
}


def json_value(value):
    if hasattr(value, "name"):
        return value.name
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


class ObservedGame:
    """Transparent proxy: forwards calls unchanged and timestamps scorer getters."""

    def __init__(self, game):
        self.inner = game
        self.trace = []
        self.lock = threading.Lock()
        self.role = threading.local()

    def __getattr__(self, name):
        value = getattr(self.inner, name)
        if name not in GETTERS or not callable(value):
            return value

        def observed(*args, **kwargs):
            start = time.perf_counter_ns()
            role = getattr(self.role, "name", threading.current_thread().name)
            try:
                result = value(*args, **kwargs)
            except BaseException as exc:
                end = time.perf_counter_ns()
                event = {
                    "role": role,
                    "thread_id": threading.get_ident(),
                    "name": name,
                    "args": [json_value(arg) for arg in args],
                    "start_ns": start,
                    "end_ns": end,
                    "status": "error",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
                with self.lock:
                    self.trace.append(event)
                raise
            end = time.perf_counter_ns()
            event = {
                "role": role,
                "thread_id": threading.get_ident(),
                "name": name,
                "args": [json_value(arg) for arg in args],
                "start_ns": start,
                "end_ns": end,
                "status": "ok",
                "value": json_value(result),
            }
            with self.lock:
                self.trace.append(event)
            return result

        return observed


def _measure_rate(edges):
    deltas = []
    for left, right in zip(edges, edges[1:]):
        tic_delta = right["tic_after"] - left["tic_after"]
        if tic_delta > 0:
            left_mid = (left["transition_lower_ns"] + left["transition_upper_ns"]) // 2
            right_mid = (right["transition_lower_ns"] + right["transition_upper_ns"]) // 2
            if right_mid > left_mid:
                deltas.append((right_mid - left_mid) / tic_delta)
    if not deltas:
        return None
    deltas.sort()
    median = deltas[len(deltas) // 2]
    return {"median_period_ns": int(median), "estimated_hz": 1e9 / median, "intervals": len(deltas)}


def run_case(case, wad_path, mode, out_file, provenance):
    game = vd.DoomGame()
    observed = ObservedGame(game)
    stop = threading.Event()
    edge_condition = threading.Condition()
    phase_edges = []
    driver_steps = []
    worker_errors = []
    load_stats = {"cycles": 0, "active_ns": 0, "thread_cpu_ns": 0}
    driver = None
    probe = None
    burner = None
    init_ok = False
    close_ok = False
    row = {
        **provenance,
        "case_id": case["case_id"],
        "sample_id": case["sample_id"],
        "episode_id": case["episode_id"],
        "session_id": case["session_id"],
        "seed": case["seed"],
        "stratum": case["stratum"],
        "phase_target_ns": case["phase_target_ns"],
        "clock_source": "dedicated empty-button advance_action(1) thread",
        "delay_control_ns": SCHEDULE["delayed_read_ns"] if case["stratum"] == "delayed_read" else 0,
        "mode": str(vd.Mode.ASYNC_SPECTATOR),
        "map": "MAP01",
        "ticrate_configured": SCHEDULE["nominal_tic_hz"],
        "available_buttons": [],
        "task_input": "none; empty ASYNC_SPECTATOR clock-advance calls only",
        "vizdoom_version": vd.__version__,
        "mode_readback": None,
        "ticrate_readback": None,
        "available_buttons_readback": None,
        "api_status": "not_started",
        "scorer_status": "not_called",
        "scorer_return": None,
        "scorer_error": None,
        "scorer_calls": [],
        "scorer_call_start_ns": None,
        "scorer_call_end_ns": None,
        "phase_anchor_edge": None,
        "phase_edges": phase_edges,
        "driver_steps": driver_steps,
        "api_trace": observed.trace,
        "driver_error": None,
        "worker_errors": worker_errors,
        "load_stats": load_stats,
        "cleanup": {"driver_stopped": False, "probe_stopped": False, "load_stopped": True, "game_closed": False},
    }

    def drive_clock():
        try:
            while not stop.is_set():
                before = int(game.get_episode_time())
                start = time.perf_counter_ns()
                game.advance_action(1)
                end = time.perf_counter_ns()
                after = int(game.get_episode_time())
                driver_steps.append({"tic_before": before, "tic_after": after, "start_ns": start, "end_ns": end, "status": "ok"})
        except BaseException as exc:
            worker_errors.append({"role": "clock_driver", "type": type(exc).__name__, "error": str(exc)})
            stop.set()

    def observe_phase():
        previous = None
        try:
            while not stop.is_set():
                start = time.perf_counter_ns()
                tic = int(game.get_episode_time())
                end = time.perf_counter_ns()
                if previous is not None and tic != previous["tic"]:
                    edge = {
                        "tic_before": previous["tic"],
                        "tic_after": tic,
                        "transition_lower_ns": previous["start_ns"],
                        "transition_upper_ns": end,
                        "previous_poll_end_ns": previous["end_ns"],
                        "current_poll_start_ns": start,
                        "current_poll_end_ns": end,
                        "poll_tic_delta": tic - previous["tic"],
                    }
                    with edge_condition:
                        phase_edges.append(edge)
                        edge_condition.notify_all()
                previous = {"tic": tic, "start_ns": start, "end_ns": end}
                time.sleep(SCHEDULE["phase_probe_sleep_ns"] / 1e9)
        except BaseException as exc:
            worker_errors.append({"role": "phase_probe", "type": type(exc).__name__, "error": str(exc)})
            stop.set()

    def cpu_load():
        cpu_start = time.thread_time_ns()
        cycle_ns = SCHEDULE["cpu_load_cycle_ns"]
        active_ns = SCHEDULE["cpu_load_active_ns"]
        try:
            while not stop.is_set():
                cycle_start = time.perf_counter_ns()
                active_until = cycle_start + active_ns
                while not stop.is_set() and time.perf_counter_ns() < active_until:
                    load_stats["cycles"] += 1
                load_stats["active_ns"] += max(0, time.perf_counter_ns() - cycle_start)
                remainder = cycle_start + cycle_ns - time.perf_counter_ns()
                if remainder > 0:
                    time.sleep(remainder / 1e9)
        except BaseException as exc:
            worker_errors.append({"role": "cpu_load", "type": type(exc).__name__, "error": str(exc)})
            stop.set()
        finally:
            load_stats["thread_cpu_ns"] = time.thread_time_ns() - cpu_start

    try:
        game.set_doom_game_path(wad_path)
        game.set_doom_map("map01")
        game.set_window_visible(False)
        game.set_sound_enabled(False)
        game.set_mode(vd.Mode.ASYNC_SPECTATOR)
        game.set_ticrate(SCHEDULE["nominal_tic_hz"])
        game.set_available_buttons([])
        game.set_episode_timeout(SCHEDULE["session_timeout_tics"])
        game.set_seed(case["seed"])
        game.init()
        init_ok = True
        game.new_episode()
        row["mode_readback"] = str(game.get_mode())
        row["ticrate_readback"] = int(game.get_ticrate())
        row["available_buttons_readback"] = [json_value(button) for button in game.get_available_buttons()]
        row["setup_status"] = "ok"
        row["api_status"] = "ok"
        row["session_start_ns"] = time.perf_counter_ns()
        driver = threading.Thread(target=drive_clock, name="empty-input-clock-driver", daemon=True)
        probe = threading.Thread(target=observe_phase, name="independent-tic-phase-probe", daemon=True)
        driver.start()
        probe.start()
        if case["stratum"] == "cpu_load":
            burner = threading.Thread(target=cpu_load, name="fixed-50pct-cpu-load", daemon=True)
            burner.start()

        deadline = time.perf_counter_ns() + SCHEDULE["phase_probe_timeout_ns"]
        with edge_condition:
            while not stop.is_set():
                tail_count = 0
                for edge in reversed(phase_edges):
                    if edge["poll_tic_delta"] != 1:
                        break
                    tail_count += 1
                if tail_count >= SCHEDULE["phase_probe_warmup_edges"]:
                    break
                remaining = deadline - time.perf_counter_ns()
                if remaining <= 0:
                    break
                edge_condition.wait(remaining / 1e9)
        stable_edges = []
        for edge in phase_edges:
            if edge["poll_tic_delta"] == 1:
                stable_edges.append(edge)
            else:
                stable_edges = []
        if len(stable_edges) < SCHEDULE["phase_probe_warmup_edges"]:
            row["setup_status"] = "STOP_NO_STABLE_TIC_TRANSITIONS"
            row["api_status"] = "insufficient_unit_tic_edges"
        else:
            anchor = stable_edges[-1]
            row["phase_anchor_edge"] = dict(anchor)
            requested_deadline_ns = anchor["transition_upper_ns"] + case["phase_target_ns"]
            target_ns = max(time.perf_counter_ns(), requested_deadline_ns)
            row["phase_target_requested_deadline_ns"] = requested_deadline_ns
            row["phase_target_deadline_ns"] = target_ns
            row["phase_target_setup_lateness_ns"] = max(0, time.perf_counter_ns() - requested_deadline_ns)
            while True:
                remaining = target_ns - time.perf_counter_ns()
                if remaining <= 0:
                    break
                time.sleep(remaining / 1e9)
            if case["stratum"] == "delayed_read":
                row["delayed_read_start_ns"] = time.perf_counter_ns()
                time.sleep(SCHEDULE["delayed_read_ns"] / 1e9)
                row["delayed_read_end_ns"] = time.perf_counter_ns()
            scorer_call_count = SCHEDULE["production_scorer_calls_per_sample"]
            for outer_attempt in range(scorer_call_count):
                role = "exact_scorer_predicate" if mode == "construction" else f"exact_scorer_predicate:{outer_attempt}"
                observed.role.name = role
                call = {"outer_attempt": outer_attempt, "role": role, "start_ns": time.perf_counter_ns(), "status": "not_called", "return": None, "error": None}
                row["phase_target_execution_lateness_ns"] = call["start_ns"] - (requested_deadline_ns + row["delay_control_ns"])
                if row["scorer_call_start_ns"] is None:
                    row["scorer_call_start_ns"] = call["start_ns"]
                try:
                    result = _coherent_progress_sample(observed, vd.GameVariable, SCHEDULE["session_timeout_tics"] / SCHEDULE["nominal_tic_hz"])
                    call["status"] = "returned"
                    call["return"] = result.as_dict()
                except BaseException as exc:
                    call["status"] = "raised"
                    call["error"] = {"type": type(exc).__name__, "error": str(exc)}
                finally:
                    call["end_ns"] = time.perf_counter_ns()
                if outer_attempt == 0:
                    row["scorer_status"] = call["status"]
                    row["scorer_return"] = call["return"]
                    row["scorer_error"] = call["error"]
                if row["scorer_calls"]:
                    call["inter_attempt_gap_ns"] = call["start_ns"] - row["scorer_calls"][-1]["end_ns"]
                row["scorer_calls"].append(call)
                row["scorer_call_end_ns"] = call["end_ns"]
            row["actual_tic_after_scorer"] = int(game.get_episode_time())
            scorer_tics = []
            for call in row["scorer_calls"]:
                events = [e for e in observed.trace if e.get("role") == call["role"]]
                scorer_tics.extend(
                    event["value"]
                    for index, event in enumerate(events)
                    if event.get("name") == "get_episode_time"
                    and (index == 0 or events[index - 1].get("name") != "get_episode_time")
                )
            required_tics = {int(tic) + delta for tic in scorer_tics for delta in (0, 1)}
            phase_deadline = time.perf_counter_ns() + SCHEDULE["phase_probe_timeout_ns"]
            with edge_condition:
                while not required_tics.issubset({edge["tic_after"] for edge in phase_edges if edge["poll_tic_delta"] == 1}) and not stop.is_set():
                    remaining = phase_deadline - time.perf_counter_ns()
                    if remaining <= 0:
                        break
                    edge_condition.wait(remaining / 1e9)
            row["phase_trace_completion_status"] = "complete" if required_tics.issubset({edge["tic_after"] for edge in phase_edges if edge["poll_tic_delta"] == 1}) else "STOP_PHASE_EDGE_UNOBSERVED"
        row["session_end_ns"] = time.perf_counter_ns()
    except BaseException as exc:
        row["setup_status"] = "STOP_SETUP_OR_INFRA"
        row["api_status"] = "error"
        row["setup_error"] = {"type": type(exc).__name__, "error": str(exc), "traceback": traceback.format_exc()}
    finally:
        stop.set()
        for thread in (burner, probe, driver):
            if thread is not None:
                thread.join(timeout=3.0)
        row["cleanup"]["load_stopped"] = burner is None or not burner.is_alive()
        row["cleanup"]["probe_stopped"] = probe is None or not probe.is_alive()
        row["cleanup"]["driver_stopped"] = driver is None or not driver.is_alive()
        if init_ok:
            try:
                game.close()
                close_ok = True
            except BaseException as exc:
                row["cleanup_error"] = {"type": type(exc).__name__, "error": str(exc)}
        row["cleanup"]["game_closed"] = close_ok
        row["clock_rate"] = _measure_rate(phase_edges)
        row["phase_edges"] = phase_edges
        row["driver_steps"] = driver_steps
        row["api_trace"] = observed.trace
        row["worker_errors"] = worker_errors
        row["load_stats"] = load_stats
        row["phase_edge_count"] = len(phase_edges)
        attempts = []
        for call in row["scorer_calls"]:
            scorer_events = [e for e in observed.trace if e.get("role") == call["role"]]
            cursor = 0
            inner_index = 0
            while cursor < len(scorer_events):
                first = scorer_events[cursor]
                if first.get("name") != "get_episode_time":
                    break
                tic = first.get("value")
                matching_edges = [e for e in phase_edges if e["tic_after"] == tic and e["poll_tic_delta"] == 1]
                estimate = None
                if matching_edges:
                    edge = max(matching_edges, key=lambda e: e["transition_upper_ns"])
                    following_edges = [
                        e for e in phase_edges
                        if e["tic_before"] == tic and e["tic_after"] == tic + 1
                        and e["poll_tic_delta"] == 1
                    ]
                    upper = edge["transition_upper_ns"]
                    next_edge = min(following_edges, key=lambda e: e["transition_lower_ns"]) if following_edges else None
                    if upper <= first["start_ns"] and next_edge is not None and next_edge["transition_lower_ns"] > first["start_ns"]:
                        estimate = {
                            "tic": tic,
                            "phase_lower_ns": max(0, first["start_ns"] - upper),
                            "phase_upper_ns": first["start_ns"] - edge["transition_lower_ns"],
                            "phase_probe_edge": edge,
                        }
                attempts.append({"outer_attempt": call["outer_attempt"], "inner_attempt": inner_index, "tic_before": tic, "phase_estimate": estimate})
                inner_index += 1
                cursor += 1
                while cursor < len(scorer_events) and scorer_events[cursor].get("name") != "get_episode_time":
                    cursor += 1
                if cursor < len(scorer_events):
                    cursor += 1
        row["attempt_phase_estimates"] = attempts
        if row.get("scorer_return"):
            row["episode_terminal_status"] = "finished" if row["scorer_return"].get("episode_finished") else "not_finished"
        elif row.get("scorer_status") == "raised":
            row["episode_terminal_status"] = "scorer_raised_before_terminal_result"
        else:
            row["episode_terminal_status"] = "no_scorer_result"
    with out_file.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(row, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("construction", "formal"), required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--wad", default="/assets/freedoom2.wad")
    parser.add_argument("--freeze-sha", default="")
    parser.add_argument("--image-id", default="")
    parser.add_argument("--freeze", default="/freeze/freeze.json")
    args = parser.parse_args()
    if not Path(args.wad).is_file():
        raise SystemExit(f"STOP_SETUP_OR_INFRA: missing WAD: {args.wad}")
    wad_sha = hashlib.sha256(Path(args.wad).read_bytes()).hexdigest()
    source_root = Path(__file__).resolve().parent
    source_names = (
        "runner.py",
        "audit.py",
        "schedule.json",
        "session_map01_v13.py",
        "map01_scorer_stdio_adapter_v1.py",
        "main_thread_scorer_polling_v1.py",
        "independent_progress_clock_v2.py",
        "Dockerfile",
        "test_audit.py",
    )
    source_hashes = {name: hashlib.sha256((source_root / name).read_bytes()).hexdigest() for name in source_names}
    freeze_path = Path(args.freeze)
    if args.mode == "formal":
        freeze_data = json.loads(freeze_path.read_text(encoding="utf-8"))
        if hashlib.sha256(freeze_path.read_bytes()).hexdigest() != args.freeze_sha:
            raise SystemExit("STOP_SETUP_OR_INFRA: freeze file hash mismatch")
        if freeze_data.get("freedoom2_wad_sha256") != wad_sha:
            raise SystemExit("STOP_SETUP_OR_INFRA: WAD hash mismatch")
        if freeze_data.get("container_image_id") != args.image_id:
            raise SystemExit("STOP_SETUP_OR_INFRA: container image id mismatch")
        for name, digest in source_hashes.items():
            if freeze_data.get("source_sha256", {}).get(name) != digest:
                raise SystemExit(f"STOP_SETUP_OR_INFRA: source hash mismatch: {name}")
    provenance = {
        "allocation_id": "issue-3300-map01-live-scorer-phase-v1" if args.mode == "formal" else "construction-excluded",
        "formal_invocation": args.mode == "formal",
        "freeze_sha256": args.freeze_sha,
        "container_image_id": args.image_id,
        "freedoom2_wad_sha256": wad_sha,
        "source_sha256": source_hashes,
    }
    out_file = Path(args.out)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    guard = out_file.with_suffix(out_file.suffix + ".invocation-guard")
    if args.mode == "formal":
        fd = os.open(guard, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump({"mode": args.mode, "freeze_sha": args.freeze_sha, "image_id": args.image_id, "started_ns": time.perf_counter_ns()}, stream, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
        cases = []
        index = 0
        for repeat in range(SCHEDULE["repeats_per_stratum_offset"]):
            for offset_index, offset in enumerate(SCHEDULE["phase_offsets_ns"]):
                for stratum in SCHEDULE["strata"]:
                    case_id = f"r{repeat:02d}-{stratum}-p{offset_index:02d}"
                    cases.append({"case_id": case_id, "sample_id": case_id, "episode_id": f"episode-{case_id}", "session_id": f"session-{case_id}", "seed": SCHEDULE["seed_base"] + index, "stratum": stratum, "phase_target_ns": offset})
                    index += 1
        if len(cases) != SCHEDULE["expected_cases"]:
            raise SystemExit("frozen schedule cardinality mismatch")
    else:
        cases = [
            {"case_id": f"construction-{stratum}", "sample_id": f"construction-{stratum}", "episode_id": f"construction-episode-{stratum}", "session_id": f"construction-session-{stratum}", "seed": SCHEDULE["seed_base"] - index - 1, "stratum": stratum, "phase_target_ns": 7142857}
            for index, stratum in enumerate(SCHEDULE["strata"])
        ]
    results = []
    for case in cases:
        results.append(run_case(case, args.wad, args.mode, out_file, provenance))
    print(json.dumps({"mode": args.mode, "rows": len(results), "output": str(out_file), "clock_progress_rows": sum(bool(r.get("phase_edges")) for r in results), "setup_stops": sum(str(r.get("setup_status", "")).startswith("STOP") for r in results), "cleanup_failures": sum(not all(r["cleanup"].values()) for r in results)}, sort_keys=True))


if __name__ == "__main__":
    main()
