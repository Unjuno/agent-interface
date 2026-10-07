#!/usr/bin/env python3
"""Run one frozen npm-packaged Codex CLI inference, with a no-retry sentinel."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"
PACKAGE = "@openai/codex@0.160.0"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    RAW.mkdir(exist_ok=True)
    invocation_path = RAW / "invocation.json"
    if invocation_path.exists():
        print("allocation already consumed or started; refusing second invocation", file=sys.stderr)
        return 3

    freeze = json.loads((ROOT / "freeze.json").read_text())
    checks = [
        (ROOT / "source.png", freeze["input"]["png_sha256"]),
        (ROOT / "source_events.jsonl", freeze["input"]["source_events_public_sha256"]),
        (ROOT / "prompt.txt", freeze["candidate"]["prompt_sha256"]),
        (ROOT / "output.schema.json", freeze["candidate"]["output_schema_sha256"]),
        (ROOT / "run_once.py", freeze["candidate"]["runner_sha256"]),
        (ROOT / "audit.py", freeze["candidate"]["auditor_sha256"]),
    ]
    for path, expected in checks:
        if not path.is_file() or sha(path) != expected:
            print(f"frozen input hash mismatch: {path.name}", file=sys.stderr)
            return 4
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
    if head != freeze["source_main_commit"]:
        print("worktree HEAD no longer matches frozen main", file=sys.stderr)
        return 5

    version_args = ["npm", "exec", "--yes", "--package", PACKAGE, "--", "codex", "--version"]
    version = subprocess.run(version_args, cwd="/tmp", capture_output=True, text=True, check=False)
    version_record = {
        "argv": version_args,
        "exit_code": version.returncode,
        "stdout": version.stdout.strip(),
    }
    (RAW / "version-preflight.json").write_text(json.dumps(version_record, indent=2) + "\n")
    expected_version = freeze["candidate"]["cli_version"]
    if version.returncode != 0 or version.stdout.strip() != expected_version:
        print("pinned npm package failed CLI version preflight; candidate not invoked", file=sys.stderr)
        return 6

    args = [
        "npm", "exec", "--yes", "--package", PACKAGE, "--",
        "codex", "exec", "--ephemeral", "--json", "--skip-git-repo-check",
        "--sandbox", "read-only", "--model", freeze["candidate"]["model"],
        "-c", f"model_reasoning_effort={freeze['candidate']['reasoning_effort']}",
        "--image", str((ROOT / "source.png").resolve()),
        "--output-schema", str((ROOT / "output.schema.json").resolve()),
        "--output-last-message", str((RAW / "final.txt").resolve()),
        "--cd", "/tmp", "-",
    ]
    prompt = (ROOT / "prompt.txt").read_bytes()
    (RAW / "prompt.stdin.txt").write_bytes(prompt)
    (RAW / "events.jsonl").touch(exist_ok=False)
    (RAW / "stderr.txt").touch(exist_ok=False)
    record = {
        "allocation": freeze["allocation"],
        "status": "started",
        "started_at_utc": now(),
        "argv": args,
        "stdin_sha256": hashlib.sha256(prompt).hexdigest(),
        "image_sha256": sha(ROOT / "source.png"),
        "package": PACKAGE,
        "cli_version": expected_version,
        "model": freeze["candidate"]["model"],
        "reasoning_effort": freeze["candidate"]["reasoning_effort"],
        "retry": "prohibited",
    }
    with invocation_path.open("x") as handle:
        json.dump(record, handle, indent=2)
        handle.write("\n")
        handle.flush()

    with (RAW / "events.jsonl").open("wb") as stdout, (RAW / "stderr.txt").open("wb") as stderr:
        try:
            completed = subprocess.run(args, input=prompt, cwd="/tmp", stdout=stdout, stderr=stderr, check=False)
            code = completed.returncode
        except BaseException as exc:
            (RAW / "launcher-error.txt").write_text(f"{type(exc).__name__}: {exc}\n")
            code = 125
    (RAW / "exit-code.txt").write_text(f"{code}\n")
    record.update({"status": "finished", "ended_at_utc": now(), "exit_code": code})
    invocation_path.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({"status": record["status"], "exit_code": code,
                      "final_present": (RAW / "final.txt").exists()}, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
