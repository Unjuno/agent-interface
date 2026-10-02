"""One-shot real ViZDoom startup/readiness candidate. No key input is issued."""
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

from PIL import Image
import vizdoom


ALLOCATION = "MAP01-ATTACK-ONSET-STARTGATE-4223-T6-20261001-01"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def rgb_digest(path: Path) -> str:
    with Image.open(path) as image:
        return digest(image.convert("RGB").tobytes())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--probe", type=Path, required=True)
    args = parser.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        raise SystemExit("STOP_CANDIDATE_OUTPUT_NOT_EMPTY")
    env = dict(os.environ)
    env.update({
        "DISPLAY": ":99", "XAUTHORITY": "/dev/null",
        "HOME": "/tmp/home", "XDG_CONFIG_HOME": "/tmp/xdg-config",
        "XDG_CACHE_HOME": "/tmp/xdg-cache", "XDG_RUNTIME_DIR": "/tmp/xdg-runtime",
        "SDL_VIDEODRIVER": "x11",
    })
    Path(env["HOME"]).mkdir(parents=True, exist_ok=True)
    for key in ("XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_RUNTIME_DIR"):
        Path(env[key]).mkdir(parents=True, exist_ok=True)
    env.pop("WAYLAND_DISPLAY", None)
    xvfb = subprocess.Popen(
        ["Xvfb", ":99", "-screen", "0", "1280x800x24", "-nolisten", "tcp", "-ac"],
        stdout=(out / "xvfb.stdout.log").open("wb"), stderr=(out / "xvfb.stderr.log").open("wb"), env=env,
    )
    openbox = None
    child = None
    stderr_thread = None
    stderr_chunks: list[str] = []
    events: list[dict] = []
    sent_commands: list[dict] = []
    started = time.monotonic()
    deadline = started + 120
    child_returncode = None
    xvfb_returncode = None
    openbox_returncode = None
    decision = "STOP_STARTUP_TIMEOUT"
    failure = None
    try:
        socket = Path("/tmp/.X11-unix/X99")
        while time.monotonic() < deadline and (xvfb.poll() is not None or not socket.exists()):
            if xvfb.poll() is not None:
                raise RuntimeError(f"Xvfb exited {xvfb.returncode}")
            time.sleep(.05)
        if not socket.exists():
            raise TimeoutError("Xvfb socket not ready")
        openbox = subprocess.Popen(
            ["openbox"], stdout=(out / "openbox.stdout.log").open("wb"),
            stderr=(out / "openbox.stderr.log").open("wb"), env=env,
        )
        source_entry = args.source / "research/doom/session_map01_v13.py"
        runtime_out = out / "runtime"
        child_argv = [sys.executable, "-B", str(source_entry), "--out", str(runtime_out),
                      "--seed", "992600", "--timeout-seconds", "60", "--skill", "1"]
        child = subprocess.Popen(child_argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True, bufsize=1, env=env, cwd="/tmp")

        def drain_stderr() -> None:
            assert child is not None and child.stderr is not None
            for line in child.stderr:
                stderr_chunks.append(line)

        stderr_thread = threading.Thread(target=drain_stderr, daemon=True)
        stderr_thread.start()
        ready = None
        first_observation = None
        post_score = None

        def read_line(timeout: float) -> str | None:
            assert child is not None and child.stdout is not None
            readable, _, _ = select.select([child.stdout], [], [], timeout)
            return child.stdout.readline() if readable else None

        command_deadline = time.monotonic() + 120
        while time.monotonic() < command_deadline:
            line = read_line(min(.25, max(0.0, command_deadline - time.monotonic())))
            if line:
                with (out / "child.stdout.jsonl").open("a", encoding="utf-8") as stream:
                    stream.write(line)
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(event, dict):
                    events.append(event)
                    if event.get("event") == "ready" and ready is None:
                        ready = event
                    if event.get("event") == "observation" and first_observation is None:
                        first_observation = event
                        if event.get("id") == "initial" and event.get("sequence") == 1 and event.get("exact") is True:
                            image = Path(event.get("image", ""))
                            if not image.is_file() or image.stat().st_size == 0:
                                raise RuntimeError("initial observation image absent/empty")
                            if not isinstance(event.get("frame_rgb_sha256"), str):
                                raise RuntimeError("initial RGB digest absent")
                            if rgb_digest(image) != event["frame_rgb_sha256"]:
                                raise RuntimeError("initial image RGB digest mismatch")
                            image_copy = out / "initial-observation.png"
                            image_copy.write_bytes(image.read_bytes())
                            if ready is not None:
                                break
                if child.poll() is not None:
                    break
            elif child.poll() is not None:
                break
            if ready is not None and first_observation is not None:
                break
        if ready is None or first_observation is None:
            raise RuntimeError("child closed/timed out before ready and initial observation")
        sent_commands.append({"op": "finish"})
        assert child.stdin is not None
        child.stdin.write(json.dumps({"op": "finish"}) + "\n")
        child.stdin.flush()
        child.stdin.close()
        finish_deadline = time.monotonic() + 30
        while time.monotonic() < finish_deadline:
            line = read_line(min(.25, max(0.0, finish_deadline - time.monotonic())))
            if line:
                with (out / "child.stdout.jsonl").open("a", encoding="utf-8") as stream:
                    stream.write(line)
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(event, dict):
                    events.append(event)
                    if event.get("event") == "post_control_score":
                        post_score = event
                        break
            elif child.poll() is not None:
                break
        try:
            child_returncode = child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            raise TimeoutError("child did not exit after finish")
        stderr_thread.join(timeout=2)
        (out / "child.stderr.txt").write_text("".join(stderr_chunks), encoding="utf-8")
        if child_returncode != 0 or post_score is None:
            raise RuntimeError(f"child exit={child_returncode}, post_control_score={post_score is not None}")
        if any(e.get("event") == "input_admission" for e in events):
            raise RuntimeError("unexpected input admission event")
        decision = "PASS_START_GATE_ONLY"
    except Exception as exc:  # retain exact one-shot failure, never retry
        failure = f"{type(exc).__name__}: {exc}"
        if child is not None and child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=3)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
        child_returncode = child.returncode if child is not None else None
        if child is not None and child.stderr is not None:
            if stderr_thread is not None:
                stderr_thread.join(timeout=2)
            (out / "child.stderr.txt").write_text("".join(stderr_chunks), encoding="utf-8")
        decision = "STOP_CANDIDATE"
    finally:
        if child is not None and child.poll() is None:
            child.kill()
            child.wait()
        for process in (openbox, xvfb):
            if process is not None and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
        xvfb_returncode = xvfb.returncode
        openbox_returncode = openbox.returncode if openbox is not None else None

    runtime_sources = out / "runtime" / "sources.json"
    raw = {
        "schema": "map01-attack-start-gate-raw-v1",
        "allocation": ALLOCATION,
        "decision": decision,
        "failure": failure,
        "environment": {k: os.environ.get(k) for k in (
            "OBSTAC_SOURCE_COMMIT", "OBSTAC_IMAGE_ID", "OBSTAC_FREEZE_SHA256",
            "OBSTAC_CONSTRUCTION", "OBSTAC_PLATFORM", "OBSTAC_DOCKER_CONTEXT",
            "OBSTAC_RUNTIME_SOURCE_BASE")},
        "platform": platform.platform(),
        "architecture": platform.machine(),
        "python": sys.version,
        "vizdoom": vizdoom.__version__,
        "runtime_artifact_id": int(os.environ["MAP01_RUNTIME_ARTIFACT_ID"]),
        "runtime_artifact_sha256": os.environ["MAP01_RUNTIME_ARTIFACT_SHA256"],
        "runtime_source_base": os.environ["OBSTAC_RUNTIME_SOURCE_BASE"],
        "candidate_invocations": 1,
        "retry_count": 0,
        "child_argv": child_argv if "child_argv" in locals() else None,
        "child_pid": child.pid if child is not None else None,
        "child_returncode": child_returncode,
        "xvfb_pid": xvfb.pid,
        "xvfb_returncode_after_cleanup": xvfb_returncode,
        "openbox_pid": openbox.pid if openbox is not None else None,
        "openbox_returncode_after_cleanup": openbox_returncode,
        "events": events,
        "sent_commands": sent_commands,
        "runtime_sources_sha256": digest(runtime_sources.read_bytes()) if runtime_sources.is_file() else None,
        "runtime_sources": json.loads(runtime_sources.read_text(encoding="utf-8"))
            if runtime_sources.is_file() else {},
        "child_stdout_sha256": digest((out / "child.stdout.jsonl").read_bytes())
            if (out / "child.stdout.jsonl").is_file() else None,
        "child_stderr_sha256": digest((out / "child.stderr.txt").read_bytes())
            if (out / "child.stderr.txt").is_file() else None,
        "xvfb_stdout_sha256": digest((out / "xvfb.stdout.log").read_bytes())
            if (out / "xvfb.stdout.log").is_file() else None,
        "xvfb_stderr_sha256": digest((out / "xvfb.stderr.log").read_bytes())
            if (out / "xvfb.stderr.log").is_file() else None,
        "openbox_stdout_sha256": digest((out / "openbox.stdout.log").read_bytes())
            if (out / "openbox.stdout.log").is_file() else None,
        "openbox_stderr_sha256": digest((out / "openbox.stderr.log").read_bytes())
            if (out / "openbox.stderr.log").is_file() else None,
        "initial_observation_png_sha256": digest((out / "initial-observation.png").read_bytes())
            if (out / "initial-observation.png").is_file() else None,
        "post_control_score_count": sum(e.get("event") == "post_control_score" for e in events),
        "input_admission_count": sum(e.get("event") == "input_admission" for e in events),
        "elapsed_seconds": round(time.monotonic() - started, 6),
    }
    (out / "RAW.json").write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if decision == "PASS_START_GATE_ONLY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
