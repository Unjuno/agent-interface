#!/usr/bin/env python3
"""Run each frozen A15 model-only case once; never retry a started case."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
MANIFEST = json.loads((ROOT / "manifest.json").read_text())
PROMPT = (ROOT / "PROMPT.txt").read_text()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    run_started = ROOT / "RUN_STARTED.json"
    outputs = ROOT / "outputs"
    if run_started.exists() or outputs.exists():
        raise SystemExit("A15 already started; do not rerun or overwrite any provider attempt")
    codex = shutil.which("codex")
    if not codex:
        raise SystemExit("codex CLI missing; no provider attempt started")
    version = subprocess.check_output([codex, "--version"], text=True).strip()
    if version != MANIFEST["codex_cli_version"]:
        raise SystemExit(f"CLI version mismatch; expected {MANIFEST['codex_cli_version']}, got {version}")
    if sha(PROMPT.encode()) != MANIFEST["frozen_files"]["PROMPT.txt"]:
        raise SystemExit("prompt hash mismatch; no provider attempt started")
    schema_path = ROOT / "result-schema.json"
    if sha(schema_path.read_bytes()) != MANIFEST["frozen_files"]["result-schema.json"]:
        raise SystemExit("schema hash mismatch; no provider attempt started")

    outputs.mkdir()
    run_started.write_text(json.dumps({
        "schema": "a15_run_started_v1",
        "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "cli": codex,
        "cli_version": version,
        "model": MANIFEST["model"],
        "effort": MANIFEST["effort"],
        "case_order": MANIFEST["case_order"],
        "attempts_per_case": 1,
    }, indent=2) + "\n")

    for case in MANIFEST["case_order"]:
        spec = MANIFEST["inputs"][case]
        image = ROOT / spec["file"]
        image_bytes = image.read_bytes()
        if sha(image_bytes) != spec["sha256"]:
            raise SystemExit(f"input hash mismatch for {case}; stopping before its model call")
        out = outputs / case
        out.mkdir()
        (out / "CALL_STARTED.json").write_text(json.dumps({
            "schema": "a15_call_started_v1",
            "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "case": case,
            "image_sha256": spec["sha256"],
            "prompt_sha256": MANIFEST["frozen_files"]["PROMPT.txt"],
            "schema_sha256": MANIFEST["frozen_files"]["result-schema.json"],
            "attempt": 1,
        }, indent=2) + "\n")
        answer = out / "answer.json"
        argv = [
            codex, "exec", "--ephemeral", "--ignore-user-config", "--ignore-rules",
            "--disable", "plugins", "--disable", "remote_plugin",
            "--disable", "shell_snapshot", "--disable", "shell_tool",
            "--sandbox", "read-only", "--json", "--color", "never",
            "--model", MANIFEST["model"],
            "-c", f'model_reasoning_effort="{MANIFEST["effort"]}"',
            "-c", "project_doc_max_bytes=0", "-c", 'approval_policy="never"',
            "--cd", str(REPO), "--output-schema", str(schema_path),
            "--output-last-message", str(answer), "--image", str(image), "-",
        ]
        (out / "argv.json").write_text(json.dumps(argv, indent=2) + "\n")
        started = dt.datetime.now(dt.timezone.utc)
        result = {"case": case, "attempt": 1, "started_utc": started.isoformat(), "timeout_seconds": MANIFEST["timeout_seconds"]}
        try:
            proc = subprocess.run(argv, input=PROMPT, text=True, capture_output=True,
                                  timeout=MANIFEST["timeout_seconds"], cwd=REPO)
            (out / "stdout.jsonl").write_text(proc.stdout)
            (out / "stderr.txt").write_text(proc.stderr)
            result.update({"returncode": proc.returncode, "timed_out": False})
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or b""
            stderr = exc.stderr or b""
            if isinstance(stdout, bytes):
                stdout = stdout.decode(errors="replace")
            if isinstance(stderr, bytes):
                stderr = stderr.decode(errors="replace")
            (out / "stdout.jsonl").write_text(stdout)
            (out / "stderr.txt").write_text(stderr)
            result.update({"returncode": None, "timed_out": True})
        result["finished_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
        result["answer_present"] = answer.is_file()
        result["answer_sha256"] = sha(answer.read_bytes()) if answer.is_file() else None
        (out / "CALL_RESULT.json").write_text(json.dumps(result, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
