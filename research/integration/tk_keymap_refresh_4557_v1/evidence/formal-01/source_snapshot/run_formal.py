#!/usr/bin/env python3
"""Single-invocation, fixed six-session Tk/XKB formal allocation."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import signal
import shutil
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RUNNER = ROOT / "smoke_xkb_tk.py"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--image-id", required=True)
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)

    snapshot_dir = args.out / "source_snapshot"
    snapshot_dir.mkdir()
    sources = sorted(path for path in ROOT.iterdir()
                     if path.is_file() and (path.suffix == ".py" or path.name == "Dockerfile"))
    for source in sources:
        shutil.copyfile(source, snapshot_dir / source.name)
    source_hashes = {path.name: sha256(path) for path in sorted(snapshot_dir.iterdir())}
    schedule = [f"tk-xkb-refresh-4664-formal-session-{index:02d}" for index in range(1, 7)]
    manifest = {
        "allocation_id": "tk-xkb-refresh-4664-formal-01",
        "formal": True,
        "invocation_count": 1,
        "retry_count": 0,
        "replacement_count": 0,
        "image_id": args.image_id,
        "expected_image_id": "sha256:4c62a3d908f6bffdbff88b28eeff305bed40f5d6fcee029b7c0a3fa2ea5a86d6",
        "image_platform": "linux/arm64",
        "hypothesis": "Existing Tk window and new Tk window both translate DE keycode 29 as z after one US-to-DE XKB change.",
        "decision_rule": {
            "pass": "six complete sessions; US map/event y; DE map z; old and fresh Tk z; balanced events and neutral key state; source/process/raw audit clean",
            "fail": "any complete session with DE server z and fresh Tk z but existing Tk not z",
            "otherwise": "HOLD_INCONSISTENT_OR_INCOMPLETE",
        },
        "source_sha256": source_hashes,
        "scheduled_sessions": schedule,
        "runner_command_template": ["python3", "smoke_xkb_tk.py", "--formal", "--allocation-id",
                                     "<session-id>", "--out", "<session-output>"],
    }
    manifest_path = args.out / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    freeze_sha = sha256(manifest_path)
    (args.out / "freeze.sha256").write_text(freeze_sha + "\n", encoding="ascii")
    if args.prepare_only:
        print(json.dumps({"manifest_sha256": freeze_sha, "manifest": manifest}, sort_keys=True))
        return 0
    tk_runtime = subprocess.run(
        [sys.executable, "-c", "import sys, tkinter, Xlib; print(f'python={sys.version.split()[0]} tkinter={tkinter.TkVersion} tcl={tkinter.TclVersion} xlib={Xlib.__version__}')"],
        text=True, capture_output=True, check=False,
    )
    versions = {
        "python": subprocess.run([sys.executable, "--version"], text=True, capture_output=True).stdout.strip()
                      or subprocess.run([sys.executable, "--version"], text=True, capture_output=True).stderr.strip(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "tk_runtime": {"returncode": tk_runtime.returncode, "stdout": tk_runtime.stdout.strip(),
                       "stderr": tk_runtime.stderr.strip()},
    }
    for binary, flag in (("Xvfb", "-help"), ("setxkbmap", "-version"), ("xkbcomp", "-version"),
                         ("xauth", "-V")):
        result = subprocess.run([binary, flag], text=True, capture_output=True, check=False)
        versions[binary] = {"returncode": result.returncode,
                            "version_line": next((line.strip() for line in
                                                  (result.stdout + "\n" + result.stderr).splitlines()
                                                  if "version" in line.lower() or binary.lower() in line.lower()), "")}
    package_versions = subprocess.run(
        ["dpkg-query", "-W", "-f=${Package}=${Version}\\n", "python3", "python3-tk", "xvfb", "xauth", "x11-xkb-utils"],
        text=True, capture_output=True, check=False,
    )
    versions["dpkg_packages"] = {"returncode": package_versions.returncode,
                                  "stdout": package_versions.stdout, "stderr": package_versions.stderr}
    (args.out / "environment.json").write_text(json.dumps(versions, indent=2, sort_keys=True) + "\n",
                                                 encoding="utf-8")

    outcomes: list[dict[str, object]] = []
    for index, allocation_id in enumerate(schedule, start=1):
        session_dir = args.out / f"session-{index:02d}"
        command = [sys.executable, str(RUNNER), "--formal", "--allocation-id", allocation_id,
                   "--out", str(session_dir)]
        started = time.monotonic_ns()
        process = subprocess.Popen(command, cwd=ROOT, env=os.environ.copy(), text=True,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   start_new_session=True)
        try:
            stdout, stderr = process.communicate(timeout=45)
            (args.out / f"session-{index:02d}.stdout.txt").write_text(stdout, encoding="utf-8")
            (args.out / f"session-{index:02d}.stderr.txt").write_text(stderr, encoding="utf-8")
            outcomes.append({"allocation_id": allocation_id, "returncode": process.returncode,
                             "started_monotonic_ns": started, "ended_monotonic_ns": time.monotonic_ns(),
                             "command": command})
        except subprocess.TimeoutExpired as exc:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                stdout, stderr = process.communicate(timeout=2)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                stdout, stderr = process.communicate()
            (args.out / f"session-{index:02d}.stdout.txt").write_text(stdout, encoding="utf-8")
            (args.out / f"session-{index:02d}.stderr.txt").write_text(stderr, encoding="utf-8")
            outcomes.append({"allocation_id": allocation_id, "returncode": process.returncode,
                             "timeout_seconds": 45, "started_monotonic_ns": started,
                             "ended_monotonic_ns": time.monotonic_ns(), "command": command})
    report = {"allocation_id": manifest["allocation_id"], "formal": True,
              "source_sha256": source_hashes, "scheduled_sessions": schedule,
              "outcomes": outcomes, "retry_count": 0, "replacement_count": 0}
    (args.out / "orchestration.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                                                 encoding="utf-8")
    evidence_hashes = {
        path.relative_to(args.out).as_posix(): sha256(path)
        for path in sorted(args.out.rglob("*"))
        if path.is_file() and path.name != "evidence_sha256.json"
    }
    (args.out / "evidence_sha256.json").write_text(
        json.dumps(evidence_hashes, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, sort_keys=True))
    return 0 if all(item.get("returncode") == 0 for item in outcomes) else 1


if __name__ == "__main__":
    raise SystemExit(main())
