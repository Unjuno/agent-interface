from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time

from runtime.backends.x11_v1.backend import X11Backend
from runtime.backends.x11_v1.session import X11RuntimeSession
from runtime.core_v1.contract import SCHEMA_PROGRAM


BASE = "f65b39b6434714a08dfa743f8f16f5cae1667f6d"
SOURCES = {
    "runtime/backends/x11_v1/backend.py": "7d996e90831c12227243393c20565d884605e088",
    "runtime/backends/x11_v1/fixture_app.py": "11c30cf084744ffdba3b00df7637b5853c8571ac",
    "runtime/backends/x11_v1/session.py": "4dbd6dd219e2ec7313cd32d3e4cb154e0efcfbb1",
}
PREFIX = "http://"
SUFFIX = "a_b"
EXPECTED = PREFIX + SUFFIX
WAIT_MS = 900
CASES = (
    ("control_us", "us", None),
    ("jp_to_us", "jp", "us"),
    ("us_to_jp", "us", "jp"),
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(argv, *, env=None, timeout=8):
    started = time.monotonic_ns()
    p = subprocess.run(argv, env=env, capture_output=True, timeout=timeout)
    return {
        "argv": argv,
        "returncode": p.returncode,
        "stdout": p.stdout.decode("utf-8", "replace"),
        "stderr": p.stderr.decode("utf-8", "replace"),
        "started_ns": started,
        "ended_ns": time.monotonic_ns(),
    }


def layout(display: str) -> dict:
    row = run(["setxkbmap", "-display", display, "-query"])
    match = re.search(r"(?m)^layout:\s*(.+?)\s*$", row["stdout"])
    row["layout"] = match.group(1) if match else None
    return row


def git_blob(repo: Path, path: str) -> str:
    return subprocess.run(["git", "hash-object", path], cwd=repo, check=True,
                          capture_output=True, text=True).stdout.strip()


def verify_sources(repo: Path) -> dict:
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, check=True,
                          capture_output=True, text=True).stdout.strip()
    ancestry = subprocess.run(["git", "merge-base", "--is-ancestor", BASE, head], cwd=repo)
    actual = {path: git_blob(repo, path) for path in SOURCES}
    if ancestry.returncode != 0 or actual != SOURCES:
        raise RuntimeError(f"source mismatch: head={head}, blobs={actual}")
    return {"head": head, "base": BASE, "blobs": actual}


def make_program(pid: str) -> dict:
    return {
        "schema": SCHEMA_PROGRAM,
        "program_id": pid,
        "source": {"observation_seq": 7, "binding_revision": 3},
        "authority": {"lease_id": "x11-keymap-5236", "expires_at_ns": time.monotonic_ns() + 30_000_000_000},
        "terminal": {"release_all_required": True},
        "ops": [
            {"op": "focus", "target": "fixture"},
            {"op": "pointer_move", "frame": "window_client", "x": 50, "y": 55},
            {"op": "pointer_button", "button": "left", "down": True},
            {"op": "pointer_button", "button": "left", "down": False},
            {"op": "text", "text": PREFIX},
            {"op": "wait_update", "timeout_ms": WAIT_MS},
            {"op": "text", "text": SUFFIX},
            {"op": "key_chord", "keys": ["CTRL", "S"]},
            {"op": "wait_update", "timeout_ms": 150},
            {"op": "release_all"},
        ],
    }


def choose_display() -> str:
    for number in range(101, 130):
        if not Path(f"/tmp/.X11-unix/X{number}").exists():
            return f":{number}"
    raise RuntimeError("no free private X display in bounded range")


def verify_keymap(display: str) -> dict:
    """Require the observable punctuation map needed by this exact text probe."""
    probe = [
        "python3", "-c",
        "from Xlib import display; import json,sys; d=display.Display(sys.argv[1]); "
        "k=d.display.info.min_keycode; m={}; "
        "[(m.setdefault(str(i),[]),m[str(i)].extend(d.keycode_to_keysym(i,l) for l in (0,1))) "
        "for i in range(k,d.display.info.max_keycode+1)]; "
        "print(json.dumps({chr(s):[i for i,v in m.items() if s in v] for s in (ord('_'),ord('/'),ord(':'))}))",
        display,
    ]
    row = run(probe)
    if row["returncode"] != 0:
        raise RuntimeError(f"keymap probe failed: {row['stderr']}")
    row["symbol_keycodes"] = json.loads(row["stdout"])
    if any(not row["symbol_keycodes"].get(symbol) for symbol in ("_", "/", ":")):
        raise RuntimeError(f"required text symbol absent from current keymap: {row['symbol_keycodes']}")
    return row


def run_case(repo: Path, out: Path, case_id: str, initial: str, target: str | None) -> dict:
    row = {"case_id": case_id, "initial_layout_requested": initial,
           "target_layout": target, "expected_text": EXPECTED, "wait_ms": WAIT_MS}
    display = choose_display()
    row["display"] = display
    case_dir = out / case_id
    case_dir.mkdir()
    meta, effect, events = (case_dir / "meta.json", case_dir / "effect.json", case_dir / "events.jsonl")
    server_log, app_log = case_dir / "xvfb.log", case_dir / "fixture.log"
    xenv = dict(os.environ, DISPLAY=display, PYTHONPATH=str(repo))
    server_stream = server_log.open("wb")
    server = subprocess.Popen(["Xvfb", display, "-screen", "0", "1024x768x24",
                               "-nolisten", "tcp", "-noreset"],
                             stdout=server_stream, stderr=subprocess.STDOUT)
    server_stream.close()
    app = None
    backend = None
    actor_state: dict = {"scheduled": target is not None}
    try:
        deadline = time.monotonic() + 5
        while not Path(f"/tmp/.X11-unix/X{display[1:]}").exists() and time.monotonic() < deadline:
            if server.poll() is not None:
                raise RuntimeError(f"Xvfb exited {server.returncode}")
            time.sleep(.05)
        if not Path(f"/tmp/.X11-unix/X{display[1:]}").exists():
            raise RuntimeError("private Xvfb socket timeout")
        row["xvfb_argv"] = ["Xvfb", display, "-screen", "0", "1024x768x24", "-nolisten", "tcp", "-noreset"]
        row["initial_set"] = run(["setxkbmap", "-display", display, "-layout", initial])
        row["initial_layout"] = layout(display)
        if row["initial_set"]["returncode"] != 0 or row["initial_layout"]["layout"] != initial:
            raise RuntimeError("initial XKB layout was not independently confirmed")
        row["initial_symbol_map"] = verify_keymap(display)

        app_stream = app_log.open("wb")
        app = subprocess.Popen([sys.executable, "-m", "runtime.backends.x11_v1.fixture_app",
                                "--meta", str(meta), "--effect", str(effect), "--events", str(events)],
                               cwd=repo, env=xenv, stdout=app_stream, stderr=subprocess.STDOUT)
        app_stream.close()
        deadline = time.monotonic() + 5
        while not meta.exists() and time.monotonic() < deadline:
            if app.poll() is not None:
                raise RuntimeError(f"fixture exited {app.returncode}")
            time.sleep(.05)
        if not meta.exists():
            raise RuntimeError("fixture metadata timeout")
        window_id = json.loads(meta.read_text(encoding="utf-8"))["window_id"]
        backend = X11Backend(display, {"fixture": window_id})
        session = X11RuntimeSession(backend)

        def remap_actor():
            time.sleep(.15)
            actor_state["started_ns"] = time.monotonic_ns()
            actor_state["argv"] = ["setxkbmap", "-display", display, "-layout", target]
            result = run(actor_state["argv"])
            actor_state.update(result)
            actor_state["ended_ns"] = time.monotonic_ns()
            actor_state["final_layout"] = layout(display)
            actor_state["symbol_map"] = verify_keymap(display)

        worker = threading.Thread(target=remap_actor, name="independent-xkb-remap") if target else None
        if worker:
            worker.start()
        row["program"] = make_program(case_id)
        row["dispatch_started_ns"] = time.monotonic_ns()
        row["dispatch"] = session.dispatch(row["program"], current_observation_seq=7,
                                            current_binding_revision=3)
        row["dispatch_ended_ns"] = time.monotonic_ns()
        if worker:
            worker.join(timeout=3)
            if worker.is_alive():
                raise RuntimeError("remap actor did not terminate")
        row["actor"] = actor_state
        row["final_layout"] = layout(display)
        row["effect_present"] = effect.exists()
        if effect.exists():
            raw_effect = effect.read_bytes()
            row["effect_sha256"] = sha256(raw_effect)
            row["effect_bytes_utf8"] = raw_effect.decode("utf-8")
        else:
            row["effect_sha256"] = None
            row["effect_bytes_utf8"] = None
        row["events_present"] = events.exists()
        row["events_sha256"] = sha256(events.read_bytes()) if events.exists() else None
        execution = row["dispatch"].get("execution", {})
        row["waits"] = execution.get("waits", [])
        row["releases"] = execution.get("releases", row["dispatch"].get("release", []))
        row["program_emissions"] = execution.get("program_emissions", row["dispatch"].get("program_emissions"))
        row["backend_emissions"] = execution.get("emissions", row["dispatch"].get("backend_emissions"))
        return row
    finally:
        if backend is not None:
            try:
                backend.close()
            except Exception:
                pass
        if app is not None:
            if app.poll() is None:
                app.terminate()
            try:
                app.wait(timeout=3)
            except subprocess.TimeoutExpired:
                app.kill()
                app.wait(timeout=3)
        if server.poll() is None:
            server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=3)
        row["app_exit"] = app.returncode if app else None
        row["xvfb_exit"] = server.returncode
        row["socket_absent_after_cleanup"] = not Path(f"/tmp/.X11-unix/X{display[1:]}").exists()
        (case_dir / "case.json").write_text(json.dumps(row, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        (case_dir / "processes.json").write_text(json.dumps({"app_exit": row["app_exit"],
            "xvfb_exit": row["xvfb_exit"], "socket_absent_after_cleanup": row["socket_absent_after_cleanup"]},
            sort_keys=True, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[3]
    out = args.output.resolve()
    if out.exists():
        raise SystemExit("output path must be new; refusing overwrite")
    source_receipt = verify_sources(repo)
    out.mkdir(parents=True)
    summary = {"allocation_id": "ISSUE5236-UBUNTU-WSL-20260928-01",
               "head": source_receipt["head"], "base": source_receipt["base"],
               "sources": source_receipt["blobs"],
               "python": sys.version, "python_xlib": importlib.metadata.version("python-xlib"),
               "argv": sys.argv, "cases": []}
    env = run(["uname", "-a"])
    summary["uname"] = env["stdout"]
    try:
        for case_id, initial, target in CASES:
            summary["cases"].append(run_case(repo, out, case_id, initial, target))
    except Exception as error:
        summary["run_error"] = repr(error)
        summary["cases"].append({"case_id": "RUN_STOP", "error": repr(error)})
    (out / "summary.json").write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return 0 if not summary.get("run_error") and [row.get("case_id") for row in summary["cases"]] == [case[0] for case in CASES] else 1


if __name__ == "__main__":
    raise SystemExit(main())
