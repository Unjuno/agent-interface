#!/usr/bin/env python3
"""Run the frozen CLI allocation at most once, persisting intent before launch."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"


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
    for path, expected in [
        (ROOT / "source.png", freeze["input"]["png_sha256"]),
        (ROOT / "source_events.jsonl", freeze["input"]["source_events_sha256"]),
        (ROOT / "prompt.txt", freeze["candidate"]["prompt_sha256"]),
        (ROOT / "output.schema.json", freeze["candidate"]["output_schema_sha256"]),
    ]:
        if sha(path) != expected:
            print(f"frozen input hash mismatch: {path.name}", file=sys.stderr)
            return 4
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
    if head != freeze["source_main_commit"]:
        print("worktree HEAD no longer matches the frozen main source", file=sys.stderr)
        return 5

    args = [
        "codex", "exec", "--ephemeral", "--json", "--skip-git-repo-check",
        "--sandbox", "read-only", "--model", freeze["candidate"]["model"],
        "-c", f"model_reasoning_effort={freeze['candidate']['reasoning_effort']}",
        "--image", str((ROOT / "source.png").resolve()),
        "--output-schema", str((ROOT / "output.schema.json").resolve()),
        "--output-last-message", str((RAW / "final.txt").resolve()),
        "--cd", "/tmp", "-",
    ]
    record = {
        "allocation": freeze["allocation"],
        "status": "started",
        "started_at_utc": now(),
        "argv": args,
        "stdin_sha256": sha(ROOT / "prompt.txt"),
        "image_sha256": sha(ROOT / "source.png"),
        "model": freeze["candidate"]["model"],
        "reasoning_effort": freeze["candidate"]["reasoning_effort"],
        "retry": "prohibited",
    }
    # O_EXCL makes the consumed-allocation sentinel atomic across accidental
    # concurrent starts. It is written before the external model request.
    with invocation_path.open("x") as handle:
        json.dump(record, handle, indent=2)
        handle.write("\n")
        handle.flush()

    prompt_bytes = (ROOT / "prompt.txt").read_bytes()
    (RAW / "prompt.stdin.txt").write_bytes(prompt_bytes)
    with \
            (RAW / "events.jsonl").open("wb") as stdout, \
            (RAW / "stderr.txt").open("wb") as stderr:
        try:
            completed = subprocess.run(args, input=prompt_bytes, stdout=stdout, stderr=stderr, check=False)
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
