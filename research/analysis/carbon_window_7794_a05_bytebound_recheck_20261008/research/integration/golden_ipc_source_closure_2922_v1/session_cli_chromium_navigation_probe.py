"""Navigate Chromium to session_v4's private fixture URL; never submit form."""
import hashlib
import json
import queue
import subprocess
import sys
import threading
import time
import urllib.parse
from pathlib import Path

ROOT = Path("/repo")
OUT = Path("/out")
SEED = 992927
IMAGE_ID = "sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393"
COMMIT = "01349d7bc76e5635f5568c53ffeec4d9ff49abb1"
CHROMIUM = "/home/taka/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome"
SOURCES = {
    "research/live_control/executor_v3.py": "ea3fa8c9751a6a41b4814ad6e0d03bec85166765b0a41d2488a51750d17b3a4a",
    "research/live_control/lease.py": "e71f9850d3999a31fcb86c00f9ef7a8ba19bae8d3a8bdc11bf7bd620817a535f",
    "research/live_control/session_v4.py": "04f06d7b787baa77cae20d0c51b563ccc4985dc19b47308d7c24318c5a9e7fee",
    "research/observation_gating/exact_gate.py": "6780624513a95039657734e76c0420447a3f9ab49f98e1f3137a19a91bc31944",
    "research/observation_gating/gui_suite.py": "953a078a06d55b9278bd7b31e176404912340a4f13407e1db343b7776645e97f",
    "research/observation_tiles/image_artifact.py": "7bf6b71d811aaefa75e87f5d9d20fd9275fc928104e910deaca9e3f00c55363e",
    "research/observation_tiles/tile_transport.py": "f74caf4f2bea59fe3a73b3f04975384d8520bb06c296765566c4dd2542ef12b0",
    "research/real_apps_v1/real_app_suite_v1.py": "22b4cc86af68a0ae866fe24735faaeefa40c0e1722238ab8c04723e1a564db24",
}

def main():
    t0 = time.monotonic_ns()
    actual = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in SOURCES}
    if actual != SOURCES:
        raise SystemExit("STOP_SOURCE_HASH_MISMATCH")
    run_out = OUT / "session"
    if run_out.exists():
        raise SystemExit("STOP_OUTPUT_PATH_PREEXISTS")
    command = [sys.executable, str(ROOT / "research/live_control/session_v4.py"),
               "--app", "chromium", "--seed", str(SEED), "--out", str(run_out),
               "--chromium", CHROMIUM]
    proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, bufsize=1)
    messages = queue.Queue()
    raw_lines = []
    events = []

    def drain_stdout():
        for line in proc.stdout:
            messages.put(line)
        messages.put(None)

    reader = threading.Thread(target=drain_stdout, daemon=True)
    reader.start()

    def next_event(timeout_s):
        try:
            line = messages.get(timeout=timeout_s)
        except queue.Empty:
            raise TimeoutError("timed out waiting for session event")
        if line is None:
            raise EOFError("session CLI exited before expected event")
        raw_lines.append(line)
        try:
            event = json.loads(line)
        except ValueError:
            return {"event": "non_json_output", "line": line.rstrip()}
        events.append(event)
        return event

    result = {
        "schema": "issue2922_session_cli_chromium_navigation_v1",
        "allocation": "issue2922-session-cli-chromium-navigation-20260928-r1",
        "seed": SEED,
        "repository_commit": COMMIT,
        "runtime_image": IMAGE_ID,
        "source_sha256": actual,
        "task_allocated": False,
        "model_calls": 0,
        "gui_input": True,
        "form_submit_steps_issued": 0,
        "server_POST_count": "not instrumented",
    }
    try:
        ready = None
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            event = next_event(max(0.01, deadline - time.monotonic()))
            if event.get("event") == "ready":
                ready = event
                break
        if ready is None:
            raise TimeoutError("session ready event not observed")
        observation = None
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            event = next_event(max(0.01, deadline - time.monotonic()))
            if event.get("event") == "observation" and event.get("id") == "initial":
                observation = event
                break
        if observation is None or observation.get("sequence") != 1:
            raise RuntimeError("exact initial observation sequence 1 not observed")
        url = ready.get("goal", {}).get("url", "")
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "http" or parsed.hostname != "127.0.0.1":
            raise RuntimeError("ready URL is not private loopback")
        result.update(ready_event=True, initial_sequence=observation["sequence"],
                      session_endpoint_host=parsed.hostname)
        steps = [
            {"op": "chord", "modifier": "Control_L", "key": "l"},
            {"op": "text", "text": url},
            {"op": "key", "key": "Return"},
            {"op": "wait_title", "contains": "AI FORM READY", "timeout_ms": 5000},
            {"op": "observe"},
        ]
        proc.stdin.write(json.dumps({
            "op": "submit", "id": "private-url-navigation-992927",
            "steps": steps, "expected_sequence": observation["sequence"],
            "valid_until_ns": time.perf_counter_ns() + 15_000_000_000,
        }) + "\n")
        proc.stdin.flush()
        terminal = None
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            event = next_event(max(0.01, deadline - time.monotonic()))
            if event.get("event") == "terminal" and event.get("id") == "private-url-navigation-992927":
                terminal = event
                break
        if terminal is None:
            proc.stdin.write(json.dumps({"op": "cancel", "id": "private-url-navigation-992927"}) + "\n")
            proc.stdin.flush()
            raise TimeoutError("navigation program terminal event not observed")
        result["executor_terminal"] = terminal
        result["accepted"] = any(e.get("event") == "accepted" for e in events)
        screenshots = [e for e in events if e.get("event") == "observation"]
        titled = [e for e in screenshots if "AI FORM READY" in str(e.get("context", ""))]
        result["chromium_title_ready_observations"] = len(titled)
        result["final_context"] = screenshots[-1].get("context") if screenshots else None
        result["request_method"] = "GET by Chromium navigation"
        result["executor_program_submissions"] = sum(
            e.get("event") == "command" and e.get("command", {}).get("op") == "submit"
            for e in events)
        result["input_admission_events"] = sum(e.get("event") == "input_admission" for e in events)
        result["form_submit_steps_issued"] = 0
        result["disposition"] = (
            "PASS_CHROMIUM_PRIVATE_ROUTE_NAVIGATION_NO_TASK"
            if terminal.get("status") == "completed"
            and terminal.get("release", {}).get("verified") is True
            and len(titled) >= 1
            else "FAIL_CHROMIUM_NAVIGATION_OR_RELEASE_GATE")
        proc.stdin.write(json.dumps({"op": "finish"}) + "\n")
        proc.stdin.flush()
        while True:
            try:
                event = next_event(10)
            except EOFError:
                break
            if event.get("event") == "independent_evaluation":
                result["independent_evaluation"] = event
                break
        result["container_exit_code"] = proc.wait(timeout=15)
        reader.join(timeout=5)
        result["event_names"] = [e.get("event") for e in events]
        result["elapsed_ms"] = (time.monotonic_ns() - t0) / 1e6
        if result["container_exit_code"] != 0:
            result["disposition"] = "FAIL_SESSION_EXIT"
        if (not result.get("independent_evaluation")
                or result["independent_evaluation"].get("success") is not False
                or "FileNotFoundError" not in result["independent_evaluation"].get("actual", {}).get("error", "")):
            result["disposition"] = "HOLD_NO_TASK_EFFECT_ORACLE_UNCLEAR"
    except Exception as exc:
        result.update(disposition="STOP_OR_FAIL_CHROMIUM_NAVIGATION",
                      error_type=type(exc).__name__, error=str(exc))
        if proc.poll() is None:
            try:
                proc.stdin.write(json.dumps({"op": "finish"}) + "\n")
                proc.stdin.flush()
                proc.wait(timeout=10)
            except Exception:
                proc.terminate()
                proc.wait(timeout=5)
        result["container_exit_code"] = proc.returncode
    finally:
        if proc.stdout:
            proc.stdout.close()
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "session_cli_stdout.jsonl").write_text("".join(raw_lines))
        (OUT / "session_cli_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0 if result.get("disposition") == "PASS_CHROMIUM_PRIVATE_ROUTE_NAVIGATION_NO_TASK" else 1

if __name__ == "__main__":
    raise SystemExit(main())
