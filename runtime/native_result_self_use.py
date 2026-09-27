"""Private X11 fixture for primary-assistant use of the public result adapter.

Run under Ubuntu with python-xlib, Pillow, tkinter and Xvfb. The assistant views
before.png and writes one request.json containing window-client point and text.
No helper model is invoked; this is not the visual target-handle bridge.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import select
from pathlib import Path
import subprocess
import sys
import time

from PIL import Image
from Xlib import X, display
from runtime.cli_v1.api import doctor
from runtime.cli_v1.golden_v3 import dispatch_golden_v3, adapt_dispatch_result
from runtime.cli_v1.observe import observe
from runtime.core_v1.contract import SCHEMA_PROGRAM


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--display-number", type=int, default=19978)
    parser.add_argument("--native-artifacts", action="store_true")
    parser.add_argument("--read-only-continuation", action="store_true")
    parser.add_argument("--native-handles", action="store_true")
    parser.add_argument("--probe-guard-focus-change", action="store_true")
    args = parser.parse_args()
    root = args.out.resolve()
    root.mkdir(parents=True, exist_ok=False)
    processes = []
    connection = None
    bridge = None
    started = time.monotonic_ns()
    try:
        # Fail before allocating a display when fixture dependencies are absent.
        import tkinter
        tkinter.Tcl()
        with (root / "xvfb.stderr").open("w") as stderr:
            if Path(f"/tmp/.X11-unix/X{args.display_number}").exists():
                raise RuntimeError("requested display already has a filesystem socket")
            xvfb = subprocess.Popen(["Xvfb", f":{args.display_number}", "-displayfd", "1", "-screen", "0",
                                      "640x360x24", "-nolisten", "tcp", "-nolisten", "unix", "-ac"],
                                     stdout=subprocess.PIPE, stderr=stderr, text=True)
            processes.append(xvfb)
            if not select.select([xvfb.stdout], [], [], 10)[0]:
                raise RuntimeError("private Xvfb startup timeout")
            number = xvfb.stdout.readline().strip()
            if not number.isdigit():
                raise RuntimeError("private Xvfb failed to allocate a display")
            if Path(f"/tmp/.X11-unix/X{number}").exists():
                raise RuntimeError("abstract display shadows a filesystem socket")
            display_name = ":" + number
        environment = dict(os.environ, DISPLAY=display_name, XAUTHORITY="")
        # The private display is used by both the fixture and the dispatch
        # facade.  Keep the parent process in the same display context; passing
        # it only to the fixture makes selector_v1 reject the otherwise live
        # X11 backend as NO_INTERACTIVE_DISPLAY.
        os.environ.update({"DISPLAY": display_name, "XAUTHORITY": ""})
        with (root / "fixture.stderr").open("w") as stderr:
            fixture = subprocess.Popen([
                sys.executable, "-m", "runtime.backends.x11_v1.fixture_app",
                "--meta", str(root / "meta.json"), "--effect", str(root / "effect.json"),
                "--events", str(root / "events.jsonl")], env=environment, stderr=stderr)
            processes.append(fixture)
        deadline = time.monotonic() + 10
        while not (root / "meta.json").exists():
            if fixture.poll() is not None or time.monotonic() > deadline:
                raise RuntimeError("fixture failed to become ready")
            time.sleep(.05)
        target = json.loads((root / "meta.json").read_text())["window_id"]
        connection = display.Display(display_name)
        window = connection.create_resource_object("window", target)

        def capture(name):
            geometry = window.get_geometry()
            pixels = window.get_image(0, 0, geometry.width, geometry.height,
                                      X.ZPixmap, 0xFFFFFFFF)
            if geometry.depth != 24 or len(pixels.data) != geometry.width * geometry.height * 4:
                raise RuntimeError("unsupported private Xvfb pixel format")
            Image.frombytes("RGB", (geometry.width, geometry.height),
                            pixels.data, "raw", "BGRX").save(root / name)

        def retained_native_image(result, name):
            observation = (result["observation"] if "observation" in result else
                           result["raw_dispatch"]["result"]["execution"]["observations"][-1])
            artifact = observation["artifact"]
            data = Path(artifact["path"]).read_bytes()
            if (hashlib.sha256(data).hexdigest() != artifact["sha256"] or
                    artifact["source_raw_sha256"] != observation["sha256"]):
                raise RuntimeError("native artifact identity mismatch")
            (root / name).write_bytes(data)

        artifact_options = {"capture_directory": str(root / "native-images")} if args.native_artifacts else {}
        if args.native_artifacts:
            initial = {
                "schema": SCHEMA_PROGRAM, "program_id": "native-source",
                "source": {"observation_seq": 1, "binding_revision": 1},
                "authority": {"lease_id": "private-source", "expires_at_ns": time.monotonic_ns()+5_000_000_000},
                "terminal": {"release_all_required": True},
                "ops": [{"op": "focus", "target": "fixture"},
                        {"op": "observe", "frame": "window_client", "x": 0, "y": 0, "w": 400, "h": 180},
                        {"op": "release_all"}],
            }
            save(root / "initial-program.json", initial)
            initial_result = dispatch_golden_v3(initial, {"fixture": target},
                current_observation_seq=1, current_binding_revision=1,
                display_name=display_name, **artifact_options)
            save(root / "initial-result.json", initial_result)
            retained_native_image(initial_result, "before.png")
        else:
            capture("before.png")
        if args.native_handles:
            if not args.native_artifacts:
                raise ValueError("native handles require native artifacts and initial focus")
            sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research/live_control"))
            from native_handle_bridge_v1 import NativeHandleBridge
            bridge = NativeHandleBridge(display_name, {"fixture": target}, "fixture", root / "bridge")
            bridge_source = bridge.observe()
            retained_native_image({"observation": bridge_source["native"]}, "before.png")
        save(root / "doctor.json", doctor(platform="linux", environ=environment))
        save(root / "ready.json", {"display": display_name, "target": target,
                                   "source_sequence": 1, "binding_revision": 1,
                                   "coordinate_frame": "screen_physical_px" if bridge else "window_client"})
        print(json.dumps({"ready": str(root / "before.png"),
                          "request": str(root / "request.json")}), flush=True)
        deadline = time.monotonic() + 240
        while not (root / "request.json").exists():
            if fixture.poll() is not None or time.monotonic() > deadline:
                raise RuntimeError("assistant request timeout or fixture exited")
            time.sleep(.05)
        request = json.loads((root / "request.json").read_text())
        point = request["point"]
        if (type(point) is not list or len(point) != 2 or
                any(type(value) is not int for value in point) or
                type(request["text"]) is not str):
            raise ValueError("explicit integer point and text required")
        program = {
            "schema": SCHEMA_PROGRAM, "program_id": "native-self-use-991078",
            "source": {"observation_seq": 1, "binding_revision": 1},
            "authority": {"lease_id": "private-self-use",
                          "expires_at_ns": time.monotonic_ns() + 5_000_000_000},
            "terminal": {"release_all_required": True},
            "ops": [
                {"op": "focus", "target": "fixture"},
                {"op": "pointer_move", "frame": "window_client", "x": point[0], "y": point[1]},
                {"op": "pointer_button", "button": "left", "down": True},
                {"op": "pointer_button", "button": "left", "down": False},
                {"op": "text", "text": request["text"]},
                {"op": "key_chord", "keys": ["CTRL", "S"]},
                {"op": "wait_update", "timeout_ms": 100},
                {"op": "observe", "frame": "window_client", "x": 0, "y": 0, "w": 400, "h": 180},
                {"op": "release_all"},
            ],
        }
        stale = dict(program, program_id="native-self-use-stale",
                     source={"observation_seq": 0, "binding_revision": 1})
        save(root / "stale-program.json", stale)
        refused = dispatch_golden_v3(stale, {"fixture": target},
            current_observation_seq=1, current_binding_revision=1, display_name=display_name)
        save(root / "stale-result.json", refused)
        save(root / "stale-effect.json", {"effect_exists": (root / "effect.json").exists()})
        save(root / "program.json", program)
        action_started = time.monotonic_ns()
        if bridge is not None:
            offset = bridge.mint("field", bridge_source["sequence"], point)
            native_result = bridge.click("field", offset, tail=program["ops"][4:-1])
            result = adapt_dispatch_result({"schema": "agent-interface/runtime-dispatch-result-v1",
                                            "status": "returned", "result": native_result})
        else:
            result = dispatch_golden_v3(program, {"fixture": target},
                current_observation_seq=1, current_binding_revision=1, display_name=display_name,
                **artifact_options)
        returned = time.monotonic_ns()
        save(root / "result.json", result)
        if args.native_artifacts:
            retained_native_image(result, "native-after.png")
        # Input completion does not mean the application's event queue is drained.
        # This is a bounded read of independent evidence, never an input retry.
        effect = None
        evidence_deadline = time.monotonic() + 2
        while time.monotonic() < evidence_deadline:
            try:
                effect = json.loads((root / "effect.json").read_text())
                break
            except (FileNotFoundError, json.JSONDecodeError):
                time.sleep(.01)
        scored = time.monotonic_ns()
        if args.probe_guard_focus_change:
            if bridge is None:
                raise ValueError("focus-change probe requires native handles")
            # Controlled private-fixture invalidation, not part of normal input.
            before_fault = bridge._binding()
            bridge.backend.root.set_input_focus(X.RevertToParent, X.CurrentTime)
            bridge.backend.d.sync()
            emissions_before = bridge.backend.emissions
            refused_reuse = bridge.click("field", offset,
                tail=[{"op": "text", "text": "mustnotrun"}])
            save(root / "guard-focus-change.json", {
                "before": before_fault, "after": bridge._binding(),
                "emissions_delta": bridge.backend.emissions-emissions_before,
                "result": refused_reuse})
        if args.read_only_continuation:
            continuation_started = time.monotonic_ns()
            continuation = observe({"fixture": target}, target="fixture", frame="window_client",
                region=[0, 0, 400, 180], capture_directory=str(root / "native-images"),
                display_name=display_name)
            save(root / "continuation.json", continuation)
            retained_native_image(continuation, "after.png")
            save(root / "continuation-timing.json", {
                "elapsed_ms": (time.monotonic_ns()-continuation_started)/1e6,
                "trigger": "independent effect read completed or bounded wait expired",
                "input_replayed": False})
        else:
            capture("after.png")
        save(root / "evaluation.json", {
            "task_success": effect == {"saved": True, "text": request["text"]},
            "actual": effect, "expected_text": request["text"],
            "source": "independent fixture effect file",
            "adapter_task_success": result["task_success"],
            "dispatch_elapsed_ms": (returned-action_started)/1e6,
            "independent_evidence_wait_ms": (scored-returned)/1e6,
            "action_to_scored_effect_ms": (scored-action_started)/1e6,
            "whole_elapsed_ms": (time.monotonic_ns()-started)/1e6,
            "helper_model_calls": 0, "primary_model_usage": None,
            "visual_target_revalidation": bridge is not None,
        })
        print(json.dumps({"result": str(root / "result.json"),
                          "evaluation": str(root / "evaluation.json")}), flush=True)
    finally:
        bridge_close_error = None
        if bridge is not None:
            try:
                bridge.close()
            except Exception as error:
                bridge_close_error = repr(error)
                save(root / "bridge-close-error.json", {"error": bridge_close_error})
        if connection is not None:
            connection.close()
        cleanup = []
        for process in reversed(processes):
            if process.poll() is None:
                process.terminate()
            try:
                code = process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                code = process.wait(timeout=5)
            cleanup.append({"pid": process.pid, "returncode": code})
        save(root / "cleanup.json", cleanup)
        if bridge_close_error is not None:
            raise RuntimeError("bridge connection cleanup failed: " + bridge_close_error)


if __name__ == "__main__":
    main()
