"""One-shot GTK decision-value runner for Issue #2107."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import select
import subprocess
import sys
import threading
import time
import traceback

from Xlib import X, XK, display

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
LIVE = ROOT / "research" / "live_control"
sys.path.insert(0, str(LIVE))

from input_owner_v10 import InputOwner as InputOwnerV10
from input_owner_v11 import InputOwner as InputOwnerV11
from policy import WAIT_NS, choose
from schedule import schedule
from xwd_state import classify

IMAGE_ID = "sha256:eb3ce9f5bd0cf358664b9d1ff9bce4cf2ce9f82f72ec700222046fb8fe8b96ba"
RELEASE_KEY = "F8"
POLL_NS = 50_000_000
RETRY_AFTER_NS = 500_000_000
ABORT_AFTER_RETRY_NS = 500_000_000
SOURCE_PATHS = (
    "research/integration/release_telemetry_gtk_route_2107_v1/README.md",
    "research/integration/release_telemetry_gtk_route_2107_v1/PREREGISTRATION.md",
    "research/integration/release_telemetry_gtk_route_2107_v1/CONSTRUCTION.md",
    "research/integration/release_telemetry_gtk_route_2107_v1/test_construction.py",
    "research/integration/release_telemetry_gtk_route_2107_v1/schedule.py",
    "research/integration/release_telemetry_gtk_route_2107_v1/runner.py",
    "research/integration/release_telemetry_gtk_route_2107_v1/fixture.py",
    "research/integration/release_telemetry_gtk_route_2107_v1/policy.py",
    "research/integration/release_telemetry_gtk_route_2107_v1/xwd_state.py",
    "research/integration/release_telemetry_gtk_route_2107_v1/audit.py",
    "research/live_control/input_owner_v10.py",
    "research/live_control/input_owner_v11.py",
    "research/live_control/executor_v3.py",
    "research/live_control/lease.py",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_jsonl(path: Path, value) -> None:
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def verify_formal_freeze(expected_commit: str) -> dict:
    freeze_path = HERE / "FREEZE.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    if len(expected_commit) != 40 or any(ch not in "0123456789abcdef" for ch in expected_commit.lower()):
        raise RuntimeError("host_frozen_commit_sha_invalid")
    if freeze.get("base_commit") != "92596bfb750be63c03d3d2906a05d5a5933651c2":
        raise RuntimeError("frozen_base_commit_mismatch")
    if freeze.get("image_id") != IMAGE_ID:
        raise RuntimeError("frozen_image_id_mismatch")
    observed = {rel: sha256(ROOT / rel) for rel in SOURCE_PATHS}
    if observed != freeze.get("source_sha256"):
        raise RuntimeError("frozen_source_hash_mismatch")
    return {"freeze_sha256": sha256(freeze_path), "source_sha256": observed,
            "frozen_commit": expected_commit, "base_commit": freeze["base_commit"]}


def wait_display(name: str, seconds: float = 5.0):
    deadline = time.monotonic() + seconds
    last = None
    while time.monotonic() < deadline:
        try:
            return display.Display(name)
        except Exception as exc:
            last = exc
            time.sleep(0.02)
    raise RuntimeError(f"xvfb_unavailable:{last!r}")


def launch_xvfb(out: Path):
    proc = subprocess.Popen(
        ["Xvfb", "-displayfd", "1", "-screen", "0", "640x360x24", "-nolisten", "tcp", "-ac", "-r"],
        stdout=subprocess.PIPE, stderr=(out / "xvfb.stderr.log").open("wb"), text=True,
    )
    if proc.stdout is None or not select.select([proc.stdout], [], [], 5)[0]:
        raise RuntimeError("xvfb_readiness_timeout")
    display_number = proc.stdout.readline().strip()
    if not display_number.isdigit():
        raise RuntimeError("xvfb_display_identity_missing")
    return proc, ":" + display_number


def private_env(display_name: str, case_dir: Path) -> dict:
    home = Path("/tmp") / ("ai2107-" + case_dir.name)
    for path in (home, home / ".config", home / ".cache", home / ".local" / "share"):
        path.mkdir(parents=True, exist_ok=True)
    return dict(os.environ, DISPLAY=display_name, HOME=str(home), XDG_CONFIG_HOME=str(home / ".config"),
                XDG_CACHE_HOME=str(home / ".cache"), XDG_DATA_HOME=str(home / ".local" / "share"),
                GSETTINGS_BACKEND="memory", NO_AT_BRIDGE="1")


def disable_autorepeat(display_name: str) -> None:
    connection = display.Display(display_name)
    try:
        connection.change_keyboard_control(auto_repeat_mode=X.AutoRepeatModeOff)
        connection.sync()
    finally:
        connection.close()


def verify_autorepeat_off(display_name: str) -> int:
    connection = display.Display(display_name)
    try:
        connection.sync()
        return int(connection.get_keyboard_control().global_auto_repeat)
    finally:
        connection.close()


def launch_fixture(case_dir: Path, env: dict, scenario: str, delay_ms: int, effect_after_press_ms: int):
    meta = case_dir / "app-meta.json"
    args = ["/usr/bin/python3", str(HERE / "fixture.py"), "--scenario", scenario,
            "--delay-ms", str(delay_ms), "--effect-after-press-ms", str(effect_after_press_ms),
            "--meta", str(meta), "--events", str(case_dir / "app-events.jsonl"),
            "--effect", str(case_dir / "effect.json")]
    proc = subprocess.Popen(args, env=env, stdout=(case_dir / "app.stdout.log").open("wb"),
                            stderr=(case_dir / "app.stderr.log").open("wb"))
    deadline = time.monotonic() + 5
    while not meta.exists():
        if proc.poll() is not None or time.monotonic() >= deadline:
            raise RuntimeError("gtk_fixture_readiness_failed")
        time.sleep(0.01)
    return proc, json.loads(meta.read_text(encoding="utf-8"))


class Lease:
    def __init__(self, focus: int, token: str):
        self.expected_focus = focus
        self.deadline = time.perf_counter_ns() + 8_000_000_000
        self.cancel = threading.Event()
        self.focus_invalid = False
        self.intent_token = token

    def check(self) -> None:
        if time.perf_counter_ns() >= self.deadline:
            raise RuntimeError("lease_expired")
        if self.cancel.is_set():
            raise RuntimeError("lease_cancelled")


def focus_window(display_name: str, xid: int) -> dict:
    connection = display.Display(display_name)
    try:
        window = connection.create_resource_object("window", xid)
        window.set_input_focus(X.RevertToParent, X.CurrentTime)
        connection.sync()
        focus = connection.get_input_focus().focus
        actual = focus.id if hasattr(focus, "id") else int(focus)
        return {"expected_focus": xid, "actual_focus": int(actual), "matches": int(actual) == xid}
    finally:
        connection.close()


def query_key_down(display_name: str) -> dict:
    connection = display.Display(display_name)
    try:
        keycode = int(connection.keysym_to_keycode(XK.string_to_keysym(RELEASE_KEY)))
        if not keycode:
            raise RuntimeError("F8_keycode_unavailable")
        bitmap = connection.query_keymap()
        down = bool(bitmap[keycode // 8] & (1 << (keycode % 8)))
        return {"key": RELEASE_KEY, "keycode": keycode, "down": down,
                "sampled_ns": time.perf_counter_ns(), "source": "XQueryKeymap"}
    finally:
        connection.close()


def events(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def normalize_receipt(raw: dict | None, owner_id: str, token: str) -> str:
    if raw is None:
        return "NO_RELEASE_RECEIPT"
    if (raw.get("event") == "input_release_rpc" and raw.get("owner_id") == owner_id
            and raw.get("intent_token") == token
            and raw.get("release_transition_interval_ns") == [raw.get("call_started_ns"), raw.get("call_returned_ns")]
            and raw.get("x11_release_and_sync_completed_before_return") is True
            and raw.get("grants_input_authority") is False):
        return "VALID_RELEASE_RECEIPT"
    return "UNKNOWN"


def capture_and_observe(case_dir: Path, case_number: int, query_number: int,
                        env: dict, xid: int, display_name: str) -> dict:
    image = case_dir / f"query-{query_number:02d}.xwd"
    started = time.perf_counter_ns()
    subprocess.run(["xwd", "-silent", "-id", str(xid), "-out", str(image)],
                   env=env, check=True, capture_output=True, timeout=5)
    finished = time.perf_counter_ns()
    return {"query_number": query_number, "capture_started_ns": started,
            "capture_finished_ns": finished, "image": image.name,
            "image_sha256": sha256(image), "visible_state": classify(image),
            "keymap": query_key_down(display_name)}


def capture_gate(case_dir: Path, gate_number: int, env: dict, xid: int,
                 display_name: str) -> dict:
    image = case_dir / f"pre-release-gate-{gate_number:02d}.xwd"
    started = time.perf_counter_ns()
    subprocess.run(["xwd", "-silent", "-id", str(xid), "-out", str(image)],
                   env=env, check=True, capture_output=True, timeout=5)
    finished = time.perf_counter_ns()
    return {"gate_number": gate_number, "capture_started_ns": started,
            "capture_finished_ns": finished, "image": image.name,
            "image_sha256": sha256(image), "visible_state": classify(image),
            "keymap": query_key_down(display_name)}


def stop_process(role: str, proc) -> dict:
    if proc is None:
        return {"role": role, "pid": None, "returncode": None}
    if proc.poll() is None:
        proc.terminate()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=2)
    return {"role": role, "pid": proc.pid, "returncode": proc.returncode}


def run_action(owner, lease: Lease, case_dir: Path, attempt: int, scenario: str,
               env: dict, xid: int, display_name: str) -> dict:
    started = time.perf_counter_ns()
    owner.call("down", lease, RELEASE_KEY)
    down_returned = time.perf_counter_ns()
    # The fixture's event log is used only to pace the frozen intervention.
    deadline = time.monotonic() + 2
    event_path = case_dir / "app-events.jsonl"
    while time.monotonic() < deadline:
        if sum(row.get("kind") == "key_press" for row in events(event_path)) >= attempt:
            break
        time.sleep(0.005)
    else:
        raise RuntimeError("gtk_key_press_not_consumed")
    gate_observations = []
    if attempt == 1 and scenario == "before":
        # For before-release rows, wait until the fixture's effect is visible
        # before releasing. This log is an intervention gate, never policy input.
        effect_deadline = time.monotonic() + 2
        gate_number = 0
        while time.monotonic() < effect_deadline:
            if not (case_dir / "effect.json").exists():
                time.sleep(0.002)
                continue
            gate_number += 1
            gate = capture_gate(case_dir, gate_number, env, xid, display_name)
            gate_observations.append(gate)
            if gate["visible_state"] == "DONE":
                break
            time.sleep(0.01)
        if not gate_observations or gate_observations[-1]["visible_state"] != "DONE":
            raise RuntimeError("pre_release_visible_effect_not_observed")
    release_started = time.perf_counter_ns()
    raw = owner.call("up", lease, RELEASE_KEY)
    caller_returned = time.perf_counter_ns()
    receipt_status = normalize_receipt(raw, owner.owner_id, lease.intent_token)
    return {"attempt": attempt, "down_call_started_ns": started, "down_call_returned_ns": down_returned,
            "release_call_started_ns": release_started, "caller_returned_ns": caller_returned,
            "receipt_raw": raw, "receipt_status": receipt_status,
            "receipt_interval_width_ns": raw.get("interval_width_ns") if isinstance(raw, dict) else None,
            "caller_after_receipt_ns": (caller_returned - raw["call_returned_ns"]
                                        if isinstance(raw, dict) else None),
            "pre_release_gate_observations": gate_observations}


def run_case(root: Path, number: int, condition: str, scenario: str, delay_ms: int,
             effect_after_press_ms: int,
             rep: int, construction: bool = False) -> dict:
    case_id = f"case-{number:03d}"
    out = root / "cases" / case_id
    out.mkdir(parents=True, exist_ok=False)
    write_json(out / "scenario.json", {"condition": condition, "scenario": scenario,
                                       "delay_ms": delay_ms, "effect_after_press_ms": effect_after_press_ms,
                                       "rep": rep, "case_id": case_id})
    processes = []
    owner = None
    x_connection = None
    result = {"case_id": case_id, "condition": condition, "scenario": scenario,
              "delay_ms": delay_ms, "effect_after_press_ms": effect_after_press_ms,
              "rep": rep, "decision_trace": [], "observations": [],
              "owner_actions": [], "status": "running"}
    try:
        xvfb, display_name = launch_xvfb(out)
        processes.append(("xvfb", xvfb))
        disable_autorepeat(display_name)
        env = private_env(display_name, out)
        app, meta = launch_fixture(out, env, scenario, delay_ms, effect_after_press_ms)
        processes.append(("gtk_app", app))
        auto_repeat = verify_autorepeat_off(display_name)
        if auto_repeat != X.AutoRepeatModeOff:
            raise RuntimeError("xvfb_autorepeat_disable_not_verified")
        xid = int(meta["window_id"])
        canvas_xid = int(meta["canvas_window_id"])
        focus = focus_window(display_name, xid)
        result.update({"display": display_name, "window_id": xid, "canvas_window_id": canvas_xid,
                       "canvas_size": [int(meta["canvas_width"]), int(meta["canvas_height"])],
                       "app_pid": int(meta["pid"]),
                       "xvfb_autorepeat": {"xvfb_r_flag": True,
                                            "global_auto_repeat_after_fixture": auto_repeat},
                       "focus_setup": focus, "app_title": meta["title"], "toolkit": meta["toolkit"]})
        if not focus["matches"]:
            raise RuntimeError("focus_setup_mismatch")
        if result["canvas_size"] != [400, 180]:
            raise RuntimeError("gtk_canvas_geometry_mismatch")
        time.sleep(0.04)
        token = f"{case_id}-intent"
        lease = Lease(xid, token)
        owner = InputOwnerV10(display_name) if condition == "NO_RELEASE_RECEIPT" else InputOwnerV11(display_name)
        first_action = run_action(owner, lease, out, 1, scenario, env, canvas_xid, display_name)
        first_action["available_to_policy_ns"] = time.perf_counter_ns()
        if condition == "AMBIGUOUS_RECEIPT":
            mutated = dict(first_action["receipt_raw"])
            mutated["intent_token"] = token + "-stale"
            first_action["receipt_presented_to_policy"] = mutated
            first_action["receipt_status"] = normalize_receipt(mutated, owner.owner_id, token)
        else:
            first_action["receipt_presented_to_policy"] = first_action["receipt_raw"]
        result["owner_actions"].append(first_action)
        for gate in first_action["pre_release_gate_observations"]:
            gate["source"] = "intervention_gate"
        receipt_status = first_action["receipt_status"]
        action_returned = True
        release_origin_ns = first_action["caller_returned_ns"]
        retries = 0
        query_number = 0
        visible_state = None
        key_down = None
        terminal = None
        # Infrastructure watchdog only; the frozen policy still retries at
        # 500 ms and aborts at 1,000 ms. Leave scheduler/capture slack here.
        case_deadline_ns = 6_000_000_000
        while terminal is None:
            elapsed = time.perf_counter_ns() - release_origin_ns
            action = choose(action_returned=action_returned, receipt_status=receipt_status,
                            visible_state=visible_state, key_down=key_down,
                            elapsed_ns=elapsed, retries=retries)
            result["decision_trace"].append({"at_ns": time.perf_counter_ns(), "action": action,
                                               "elapsed_ns": elapsed, "receipt_status": receipt_status,
                                               "action_returned": action_returned,
                                               "visible_state": visible_state, "key_down": key_down,
                                               "retries": retries})
            if action == "QUERY":
                result["decision_trace"][-1]["consumed_observation_number"] = query_number + 1
            elif action == "RETRY":
                result["decision_trace"][-1]["consumed_retry_attempt"] = retries + 2
            if action in ("CONTINUE", "ABORT"):
                terminal = action
            elif action == "QUERY":
                query_number += 1
                observation = capture_and_observe(out, number, query_number, env, canvas_xid, display_name)
                observation["available_to_policy_ns"] = time.perf_counter_ns()
                result["observations"].append(observation)
                visible_state = observation["visible_state"]
                key_down = observation["keymap"]["down"]
            elif action == "WAIT":
                result["decision_trace"][-1]["wait_requested_ns"] = time.perf_counter_ns()
                remaining = WAIT_NS
                if retries == 0:
                    remaining = min(remaining, max(1, RETRY_AFTER_NS - elapsed))
                else:
                    limit = RETRY_AFTER_NS + ABORT_AFTER_RETRY_NS
                    remaining = min(remaining, max(1, limit - elapsed))
                result["decision_trace"][-1]["wait_requested_duration_ns"] = remaining
                time.sleep(remaining / 1e9)
                result["decision_trace"][-1]["wait_completed_ns"] = time.perf_counter_ns()
                visible_state = None
                key_down = None
            elif action == "RETRY":
                retries += 1
                retry = run_action(owner, lease, out, retries + 1, scenario, env, canvas_xid, display_name)
                result["owner_actions"].append(retry)
                if condition == "AMBIGUOUS_RECEIPT":
                    mutated = dict(retry["receipt_raw"])
                    mutated["intent_token"] = token + "-stale"
                    retry["receipt_presented_to_policy"] = mutated
                    retry["receipt_status"] = normalize_receipt(mutated, owner.owner_id, token)
                else:
                    retry["receipt_presented_to_policy"] = retry["receipt_raw"]
                receipt_status = retry["receipt_status"]
                retry["available_to_policy_ns"] = time.perf_counter_ns()
                visible_state = None
                key_down = None
            else:
                raise RuntimeError(f"unknown_policy_action:{action}")
            if time.perf_counter_ns() - release_origin_ns > case_deadline_ns:
                raise RuntimeError("policy_case_deadline_exceeded")
        decision_returned_ns = time.perf_counter_ns()
        owner_state = owner.call("input_state")
        # Capture terminal keymap independently after the policy decision.
        terminal_keymap = query_key_down(display_name)
        app_rows = events(out / "app-events.jsonl")
        effect = json.loads((out / "effect.json").read_text(encoding="utf-8")) if (out / "effect.json").exists() else None
        result.update({"status": "completed", "terminal_action": terminal,
                       "owner_id": owner.owner_id,
                       "decision_returned_ns": decision_returned_ns,
                       "decision_latency_ns": decision_returned_ns - first_action["caller_returned_ns"],
                       "retry_count": retries, "policy_query_count": query_number,
                       "terminal_keymap": terminal_keymap, "owner_state": owner_state,
                       "app_events": app_rows, "effect_oracle": effect,
                       "false_continue_candidate": terminal == "CONTINUE" and effect is None,
                       "model_calls": 0, "provider_calls": 0, "tokens": 0})
        write_json(out / "result.json", result)
        return result
    except BaseException as exc:
        write_json(out / "case-stop.json", {"status": "STOP", "case_id": case_id,
                                             "error": repr(exc), "traceback": traceback.format_exc(),
                                             "partial_result": result})
        raise
    finally:
        cleanup = []
        if owner is not None:
            try:
                owner.close()
                cleanup.append({"role": "input_owner", "closed": True,
                                "stopped": owner.stopped.is_set(), "records": owner.records})
            except BaseException as exc:
                cleanup.append({"role": "input_owner", "closed": False, "error": repr(exc),
                                "stopped": owner.stopped.is_set(), "records": owner.records})
        for role, proc in reversed(processes):
            cleanup.append(stop_process(role, proc))
        write_json(out / "cleanup.json", cleanup)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("construction", "formal"), required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--freeze-commit")
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    if args.mode == "formal":
        if not args.freeze_commit:
            raise RuntimeError("formal_requires_frozen_commit")
        freeze_info = verify_formal_freeze(args.freeze_commit)
    else:
        freeze_info = None
    cases = []
    try:
        for index, (condition, scenario, delay, press_delay, rep) in enumerate(schedule(args.mode), 1):
            cases.append(run_case(out, index, condition, scenario, delay, press_delay, rep,
                                  construction=args.mode == "construction"))
    except BaseException as exc:
        write_json(out / "runner-stop.json", {"status": "STOP", "mode": args.mode,
                                              "completed_cases": len(cases),
                                              "case_count": len(schedule(args.mode)),
                                              "error": repr(exc), "traceback": traceback.format_exc()})
        raise
    summary = {"allocation": "issue2107-gtk-release-decision-" + args.mode + "-01",
               "status": "RUN_COMPLETED_PENDING_INDEPENDENT_AUDIT", "mode": args.mode,
               "case_count": len(cases), "completed_cases": len(cases), "formal_reruns": 0,
               "cases": [f"cases/{row['case_id']}/result.json" for row in cases],
               "source_root_commit": freeze_info["frozen_commit"] if freeze_info else None,
               "freeze": freeze_info, "image_id": IMAGE_ID,
               "image_platform": "linux/amd64", "root_read_only": True,
               "platform": platform.platform(), "python": sys.version,
               "network": "none (required by invocation)", "source_read_only": True,
               "model_calls": sum(row["model_calls"] for row in cases),
               "provider_calls": sum(row["provider_calls"] for row in cases),
               "tokens": sum(row["tokens"] for row in cases)}
    write_json(out / "runner-summary.json", summary)
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
