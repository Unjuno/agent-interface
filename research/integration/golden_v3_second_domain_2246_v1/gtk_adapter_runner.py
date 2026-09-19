"""Bounded GTK/X11 adapter runner for #2492.

This is research-only. It runs the existing X11 backend and golden-v3 adapter
against the GTK fixture; it does not invoke a model/provider.
"""
import argparse
import json
import os
import select
import subprocess
import sys
import time
from pathlib import Path

# Keep the research runner runnable from any working directory.
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime.cli_v1.golden_v3 import dispatch_golden_v3
from runtime.core_v1.contract import SCHEMA_PROGRAM


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    root = args.out.resolve()
    root.mkdir(parents=True, exist_ok=False)
    processes = []
    display_name = None
    try:
        xvfb = subprocess.Popen(
            ["Xvfb", "-displayfd", "1", "-screen", "0", "640x360x24",
             "-nolisten", "tcp", "-ac"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        processes.append(xvfb)
        if not select.select([xvfb.stdout], [], [], 10)[0]:
            raise RuntimeError("Xvfb startup timeout")
        number = xvfb.stdout.readline().strip()
        if not number.isdigit():
            raise RuntimeError("Xvfb did not return a display number")
        display_name = ":" + number
        env = dict(os.environ, DISPLAY=display_name)
        # The fixture needs DISPLAY in its child environment, while the
        # promoted selector also reads the runner process environment.
        os.environ["DISPLAY"] = display_name
        fixture = subprocess.Popen(
            [sys.executable,
             "research/integration/golden_v3_second_domain_2246_v1/gtk_fixture_app.py",
             "--meta", str(root / "meta.json"),
             "--effect", str(root / "effect.json"),
             "--events", str(root / "events.jsonl")],
            env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        processes.append(fixture)
        deadline = time.monotonic() + 10
        while not (root / "meta.json").exists():
            if fixture.poll() is not None or time.monotonic() > deadline:
                raise RuntimeError("GTK fixture did not become ready")
            time.sleep(.02)
        target = json.loads((root / "meta.json").read_text())["window_id"]

        authority = {
            "lease_id": "gtk-preflight-2492",
            "expires_at_ns": time.monotonic_ns() + 10_000_000_000,
        }
        program = {
            "schema": SCHEMA_PROGRAM,
            "program_id": "gtk-golden-v3-preflight",
            "source": {"observation_seq": 1, "binding_revision": 1},
            "authority": authority,
            "terminal": {"release_all_required": True},
            "ops": [
                {"op": "focus", "target": "fixture"},
                {"op": "pointer_move", "frame": "window_client", "x": 60, "y": 45},
                {"op": "pointer_button", "button": "left", "down": True},
                {"op": "pointer_button", "button": "left", "down": False},
                {"op": "text", "text": "gtk2492"},
                {"op": "key_chord", "keys": ["CTRL", "s"]},
                {"op": "wait_update", "timeout_ms": 100},
                {"op": "observe", "frame": "window_client", "x": 0, "y": 0, "w": 400, "h": 180},
                {"op": "release_all"},
            ],
        }
        stale = dict(program, program_id="gtk-golden-v3-stale",
                     source={"observation_seq": 0, "binding_revision": 1})
        stale_result = dispatch_golden_v3(
            stale, {"fixture": target}, current_observation_seq=1,
            current_binding_revision=1, display_name=display_name)
        save(root / "stale-result.json", stale_result)

        started = time.monotonic_ns()
        result = dispatch_golden_v3(
            program, {"fixture": target}, current_observation_seq=1,
            current_binding_revision=1, display_name=display_name)
        returned = time.monotonic_ns()
        save(root / "result.json", result)

        effect = None
        for _ in range(200):
            try:
                effect = json.loads((root / "effect.json").read_text())
                break
            except (FileNotFoundError, json.JSONDecodeError):
                time.sleep(.01)
        evaluation = {
            "adapter_result": result,
            "independent_effect": effect,
            "task_success": effect == {"saved": True, "text": "gtk2492"},
            "stale_refusal": stale_result.get("status") == "refused",
            "stale_error": stale_result.get("diagnostic") or stale_result.get("raw_dispatch", {}).get("result", {}).get("error"),
            "dispatch_elapsed_ms": (returned - started) / 1e6,
            "model_calls": 0,
            "provider_calls": 0,
            "scope": "GTK/X11 bounded adapter preflight; not full #2492 acceptance",
        }
        save(root / "evaluation.json", evaluation)
        print(json.dumps(evaluation, indent=2, sort_keys=True))
    finally:
        for process in reversed(processes):
            if process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


if __name__ == "__main__":
    main()
