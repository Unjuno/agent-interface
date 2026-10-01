#!/usr/bin/env python3
"""One-pass XGetImage String8 experiment and disjoint construction probe."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import secrets
import selectors
import subprocess
import sys
import tempfile
import time

from Xlib import X
from Xlib.display import Display

from case_app import pixels
from native_ximage import capture as native_capture
from normalize import normalize

ROOT = Path(__file__).resolve().parents[1]
SCHEDULE = ROOT / "SCHEDULE.json"
APP = Path(__file__).with_name("case_app.py")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def formal_cases() -> list[dict]:
    schedule = json.loads(SCHEDULE.read_text(encoding="utf-8"))
    result = []
    for repetition in schedule["repetitions"]:
        for pattern in schedule["patterns"]:
            for target in schedule["targets"]:
                index = len(result)
                result.append({"index": index, "case_id": f"{repetition:02d}-{pattern}-{target}", "repetition": repetition, "pattern": pattern, "target": target, "width": schedule["width"], "height": schedule["height"]})
    return result


def stop(proc: subprocess.Popen | None, timeout: float = 3.0) -> int | None:
    if proc is None:
        return None
    if proc.poll() is None:
        proc.terminate()
    try:
        return proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        return proc.wait(timeout=timeout)


def run_case(case: dict, display_number: int) -> dict:
    record = {"case": case, "status": "STARTED"}
    with tempfile.TemporaryDirectory(prefix="x11-string8-case-") as temp_name:
        temp = Path(temp_name)
        auth = temp / "Xauthority"
        auth.touch(mode=0o600)
        os.chmod(auth, 0o600)
        display_name = f":{display_number}"
        auth_result = subprocess.run(["xauth", "-f", str(auth), "add", display_name, ".", secrets.token_hex(16)], capture_output=True, text=True, check=False)
        if auth_result.returncode:
            return {**record, "status": "XAUTH_FAILURE", "xauth_exit": auth_result.returncode}
        env = os.environ.copy()
        env.update({"DISPLAY": display_name, "XAUTHORITY": str(auth), "LC_ALL": "C.UTF-8"})
        server = subprocess.Popen(["Xvfb", display_name, "-screen", "0", "64x64x24", "-nolisten", "tcp", "-auth", str(auth)], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, env=env)
        record["xvfb_pid"] = server.pid
        fixture = None
        try:
            socket_path = Path("/tmp/.X11-unix") / f"X{display_number}"
            deadline = time.monotonic() + 5.0
            while time.monotonic() < deadline and not socket_path.exists():
                if server.poll() is not None:
                    break
                time.sleep(0.01)
            if server.poll() is not None or not socket_path.exists():
                return {**record, "status": "XVFB_START_FAILURE", "xvfb_exit_before_case": server.poll()}
            fixture = subprocess.Popen([sys.executable, str(APP), "--target", case["target"], "--pattern", case["pattern"], "--width", str(case["width"]), "--height", str(case["height"])], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, env=env)
            record["fixture_pid"] = fixture.pid
            selector = selectors.DefaultSelector()
            selector.register(fixture.stdout, selectors.EVENT_READ)
            if not selector.select(timeout=5.0):
                return {**record, "status": "FIXTURE_READY_TIMEOUT", "fixture_exit": fixture.poll()}
            ready = json.loads(fixture.stdout.readline())
            selector.close()
            old_display = os.environ.get("DISPLAY")
            old_xauthority = os.environ.get("XAUTHORITY")
            os.environ.update({"DISPLAY": display_name, "XAUTHORITY": str(auth)})
            try:
                client = Display(display_name)
                try:
                    drawable = client.create_resource_object("drawable", ready["drawable_id"])
                    reply = drawable.get_image(0, 0, case["width"], case["height"], X.ZPixmap, 0xFFFFFFFF)
                    client.sync()
                    payload = reply.data
                    python_type = "str" if isinstance(payload, str) else "bytes"
                    represented = normalize(payload)
                    try:
                        legacy = bytes(payload)
                        legacy_error = None
                        legacy_b64 = b64(legacy)
                    except Exception as exc:
                        legacy_error = {"type": type(exc).__name__, "message": str(exc)}
                        legacy_b64 = None
                    candidate = normalize(payload)
                    native = native_capture(ready["drawable_id"], case["width"], case["height"], display_name)
                finally:
                    client.close()
            finally:
                if old_display is None:
                    os.environ.pop("DISPLAY", None)
                else:
                    os.environ["DISPLAY"] = old_display
                if old_xauthority is None:
                    os.environ.pop("XAUTHORITY", None)
                else:
                    os.environ["XAUTHORITY"] = old_xauthority
            record.update(status="CAPTURED", drawable_id=int(ready["drawable_id"]), source_pixels=ready["pixels"], python_data_type=python_type, python_data_text=payload if isinstance(payload, str) else None, python_data_bytes_b64=b64(payload) if isinstance(payload, bytes) else None, representation_b64=b64(represented), representation_sha256=sha256(represented), legacy_error=legacy_error, legacy_bytes_b64=legacy_b64, candidate_bytes_b64=b64(candidate), candidate_sha256=sha256(candidate), native_bytes_b64=b64(native["raw"]), native_sha256=sha256(native["raw"]), native_pixels=native["pixels"], geometry={key: native[key] for key in ("width", "height", "depth", "bits_per_pixel", "bytes_per_line", "byte_order")}, display=display_name, tcp_listening=False, xauthority_mode=oct(auth.stat().st_mode & 0o777))
            fixture.stdin.write("stop\n")
            fixture.stdin.flush()
            record["fixture_exit"] = fixture.wait(timeout=3.0)
            record["status"] = "COMPLETE"
            return record
        finally:
            if fixture is not None:
                if fixture.poll() is None:
                    stop(fixture)
                if fixture.stdout:
                    fixture.stdout.close()
                if fixture.stderr:
                    record["fixture_stderr"] = fixture.stderr.read()
                    fixture.stderr.close()
            record["xvfb_exit"] = stop(server)
            if server.stderr:
                record["xvfb_stderr"] = server.stderr.read()
                server.stderr.close()
            record["cleanup_complete"] = server.poll() is not None and (fixture is None or fixture.poll() is not None)


def run(cases: list[dict], out: Path, display_base: int) -> dict:
    out.mkdir(parents=True, exist_ok=False)
    raw_path = out / "raw.jsonl"
    rows = []
    with raw_path.open("w", encoding="utf-8", newline="\n") as stream:
        for case in cases:
            row = run_case(case, display_base + int(case["index"]))
            rows.append(row)
            stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
            stream.flush()
    summary = {"scheduled": len(cases), "completed": sum(row.get("status") == "COMPLETE" for row in rows), "failed": sum(row.get("status") != "COMPLETE" for row in rows), "string_payloads": sum(row.get("python_data_type") == "str" for row in rows), "bytes_payloads": sum(row.get("python_data_type") == "bytes" for row in rows), "legacy_type_errors": sum((row.get("legacy_error") or {}).get("type") == "TypeError" for row in rows), "candidate_native_mismatches": sum(row.get("candidate_bytes_b64") != row.get("native_bytes_b64") for row in rows), "pixel_oracle_mismatches": sum(row.get("source_pixels") != row.get("native_pixels") for row in rows), "raw_sha256": sha256(raw_path.read_bytes())}
    (out / "summary.json").write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--construction", action="store_true")
    mode.add_argument("--formal", action="store_true")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    schedule = json.loads(SCHEDULE.read_text(encoding="utf-8"))
    if args.construction:
        cases = [dict(index=i, **case) for i, case in enumerate(schedule["construction_cases"])]
        display_base = 12000
    else:
        cases = formal_cases()
        display_base = 13000
    summary = run(cases, args.out, display_base)
    summary["classification"] = "EXCLUDED_CONSTRUCTION_ONLY" if args.construction else "ONE_FROZEN_FORMAL_ALLOCATION"
    (args.out / "summary.json").write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["failed"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
