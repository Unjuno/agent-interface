"""Two-session live-app effect vs render-only GTK decoy diagnostic."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.cli_v1.golden_v3 import dispatch_golden_v3
from runtime.core_v1.contract import SCHEMA_PROGRAM

FIXTURE = ROOT / "research/integration/golden_v3_second_domain_2246_v1/gtk_fixture_app.py"
DECOY = ROOT / "research/integration/gtk_effect_control_3240_v1/fixture_render_decoy.py"
TEXT = "gtk3240"


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def xwd(env, xid, path):
    subprocess.run(["xwd", "-silent", "-id", str(xid), "-out", str(path)],
                   env=env, check=True, capture_output=True, timeout=10)


def identity(env, xid):
    props = subprocess.run(["xprop", "-id", str(xid), "_NET_WM_PID", "WM_NAME", "WM_CLASS"],
                           env=env, check=True, text=True, capture_output=True, timeout=5).stdout
    geom = subprocess.run(["xwininfo", "-id", str(xid)], env=env,
                          check=True, text=True, capture_output=True, timeout=5).stdout
    return {"xid": int(xid), "xprop": props, "xwininfo": geom}


def launch_fixture(out, display):
    home = Path("/tmp") / ("gtk3240-" + out.name)
    for subdir in (home, home / ".config", home / ".cache", home / ".local" / "share"):
        subdir.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, DISPLAY=display, HOME=str(home),
               XDG_CONFIG_HOME=str(home / ".config"),
               XDG_CACHE_HOME=str(home / ".cache"),
               XDG_DATA_HOME=str(home / ".local" / "share"),
               GSETTINGS_BACKEND="memory", NO_AT_BRIDGE="1")
    proc = subprocess.Popen([
        "/usr/bin/python3", str(FIXTURE), "--mode", "useful",
        "--meta", str(out / "app-meta.json"),
        "--effect", str(out / "effect.json"),
        "--events", str(out / "app-events.jsonl"),
    ], env=env, stdout=(out / "app.stdout").open("wb"),
       stderr=(out / "app.stderr").open("wb"))
    deadline = time.monotonic() + 10
    while not (out / "app-meta.json").exists():
        if proc.poll() is not None or time.monotonic() >= deadline:
            raise RuntimeError("target GTK fixture readiness STOP")
        time.sleep(0.02)
    return env, proc, json.loads((out / "app-meta.json").read_text())


def launch_xvfb(out):
    proc = subprocess.Popen(
        ["Xvfb", "-displayfd", "1", "-screen", "0", "640x360x24",
         "-nolisten", "tcp", "-ac"], stdout=subprocess.PIPE,
        stderr=(out / "xvfb.stderr").open("wb"), text=True)
    if not select.select([proc.stdout], [], [], 10)[0]:
        raise RuntimeError("Xvfb readiness STOP")
    value = proc.stdout.readline().strip()
    if not value.isdigit():
        raise RuntimeError("Xvfb display identity STOP")
    return proc, ":" + value


def program(program_id, ops):
    return {
        "schema": SCHEMA_PROGRAM,
        "program_id": program_id,
        "source": {"observation_seq": 1, "binding_revision": 1},
        "authority": {"lease_id": program_id,
                      "expires_at_ns": time.monotonic_ns() + 10_000_000_000},
        "terminal": {"release_all_required": True},
        "ops": ops + [{"op": "release_all"}],
    }


def dispatch(env, display, xid, program_id, ops):
    old = os.environ.get("DISPLAY")
    os.environ["DISPLAY"] = display
    try:
        return dispatch_golden_v3(
            program(program_id, ops), {"fixture": xid},
            current_observation_seq=1, current_binding_revision=1,
            display_name=display)
    finally:
        if old is None:
            os.environ.pop("DISPLAY", None)
        else:
            os.environ["DISPLAY"] = old


def stop_all(processes):
    results = []
    for role, proc in reversed(processes):
        if proc.poll() is None:
            proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=3)
        results.append({"role": role, "pid": proc.pid, "returncode": proc.returncode})
    return results


def one_session(root, name, decoy=False):
    out = root / name
    out.mkdir()
    processes = []
    try:
        xvfb, display = launch_xvfb(out)
        processes.append(("xvfb", xvfb))
        env, app, meta = launch_fixture(out, display)
        processes.append(("target_app", app))
        target = int(meta["window_id"])
        write_json(out / "target_identity_pre.json", identity(env, target))
        xwd(env, target, out / "target_pre.xwd")
        measured_pre_image = out / "target_pre.xwd"

        if decoy:
            decoy_proc = subprocess.Popen([
                "/usr/bin/python3", str(DECOY), "--meta", str(out / "decoy-meta.json"),
                "--text", TEXT,
            ], env=env, stdout=(out / "decoy.stdout").open("wb"),
               stderr=(out / "decoy.stderr").open("wb"))
            processes.append(("render_decoy", decoy_proc))
            deadline = time.monotonic() + 10
            while not (out / "decoy-meta.json").exists():
                if decoy_proc.poll() is not None or time.monotonic() >= deadline:
                    raise RuntimeError("render-only decoy readiness STOP")
                time.sleep(0.02)
            decoy_xid = int(json.loads((out / "decoy-meta.json").read_text())["window_id"])
            write_json(out / "decoy_identity.json", identity(env, decoy_xid))
            xwd(env, decoy_xid, out / "decoy_saved_looking.xwd")
            xwd(env, target, out / "target_post.xwd")
            adapter_results = []
        else:
            prep = dispatch(env, display, target, "effect-prep", [
                {"op": "focus", "target": "fixture"},
                {"op": "pointer_move", "frame": "window_client", "x": 60, "y": 45},
                {"op": "pointer_button", "button": "left", "down": True},
                {"op": "pointer_button", "button": "left", "down": False},
                {"op": "text", "text": TEXT},
                {"op": "wait_update", "timeout_ms": 50},
                {"op": "observe", "frame": "window_client", "x": 0, "y": 0, "w": 400, "h": 180},
            ])
            write_json(out / "adapter-prep.json", prep)
            xwd(env, target, out / "target_ready_pre_action.xwd")
            measured_pre_image = out / "target_ready_pre_action.xwd"
            action = dispatch(env, display, target, "effect-save", [
                {"op": "focus", "target": "fixture"},
                {"op": "key_chord", "keys": ["CTRL", "s"]},
                {"op": "wait_update", "timeout_ms": 100},
                {"op": "observe", "frame": "window_client", "x": 0, "y": 0, "w": 400, "h": 180},
            ])
            write_json(out / "adapter-action.json", action)
            deadline = time.monotonic() + 2
            while not (out / "effect.json").exists() and time.monotonic() < deadline:
                time.sleep(0.01)
            xwd(env, target, out / "target_post.xwd")
            adapter_results = [prep, action]

        write_json(out / "target_identity_post.json", identity(env, target))
        row = {
            "case": "RENDER_ONLY_DECOY" if decoy else "APPLICATION_SAVE",
            "display": display,
            "target_window_id": target,
            "target_pid": app.pid,
            "adapter_results": [x.get("status") for x in adapter_results],
            "effect_present": (out / "effect.json").exists(),
            "event_lines": (out / "app-events.jsonl").read_text().splitlines()
                           if (out / "app-events.jsonl").exists() else [],
            "target_initial_sha256": sha(out / "target_pre.xwd"),
            "target_pre_sha256": sha(measured_pre_image),
            "target_post_sha256": sha(out / "target_post.xwd"),
            "target_identity_same": (out / "target_identity_pre.json").read_bytes()
                                    == (out / "target_identity_post.json").read_bytes(),
        }
        if decoy:
            row["decoy_window_id"] = decoy_xid
            row["decoy_pid"] = decoy_proc.pid
            row["decoy_sha256"] = sha(out / "decoy_saved_looking.xwd")
            row["visual_only_would_accept"] = row["decoy_sha256"] != row["target_pre_sha256"]
        write_json(out / "row.json", row)
    finally:
        processes_final = stop_all(processes)
        write_json(out / "processes.json", processes_final)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    root = args.out.resolve()
    root.mkdir(parents=True, exist_ok=False)
    freeze = ROOT / "research/integration/gtk_effect_control_3240_v1/FREEZE.json"
    if freeze.exists():
        (root / "freeze.json").write_bytes(freeze.read_bytes())
    try:
        one_session(root, "01_application_save", decoy=False)
        one_session(root, "02_render_only_decoy", decoy=True)
    except Exception as exc:
        write_json(root / "runner-stop.json", {
            "decision": "STOP_RUNNER_EXCEPTION",
            "error": repr(exc),
            "completed_rows": [str(path.relative_to(root)) for path in sorted(root.glob("*/row.json"))],
            "scope": "two-row diagnostic; no retry",
        })
        raise
    summary = {
        "allocation": "issue3240-gtk-app-effect-control-v1",
        "decision": "RUN_COMPLETED_PENDING_INDEPENDENT_AUDIT",
        "sessions": 2,
        "reruns": 0,
        "rows": ["01_application_save/row.json", "02_render_only_decoy/row.json"],
        "scope": "first-rung diagnostic; not formal #2606 acceptance",
        "model_calls": 0,
        "provider_calls": 0,
    }
    write_json(root / "runner-summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
