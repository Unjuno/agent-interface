"""Execute seven bounded real-process broker cases and retain all raw evidence."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback

SRC = Path("/src")
OUT = Path("/out")
BROKER = SRC / "host_model_ipc_broker_v1.py"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n",
                    encoding="utf-8")


def make_fake(path: Path) -> None:
    path.write_text(
        "#!" + sys.executable + "\n"
        "import json, os, sys, time\n"
        "record={'argv':sys.argv[1:], 'stdin':sys.stdin.read()}\n"
        "with open(os.environ['FAKE_CALL_LOG'],'a',encoding='utf-8') as f:"
        " f.write(json.dumps(record,sort_keys=True)+'\\n')\n"
        "time.sleep(float(os.environ.get('FAKE_SLEEP','0')))\n"
        "print(os.environ.get('FAKE_RESPONSE','fake-response'))\n"
        "raise SystemExit(int(os.environ.get('FAKE_EXIT','0')))\n",
        encoding="utf-8", newline="\n")
    path.chmod(0o755)


def snapshot(path: Path) -> dict:
    files = {}
    if path.exists():
        for item in sorted(path.iterdir()):
            if item.is_file():
                try:
                    files[item.name] = item.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    files[item.name] = {"sha256": digest(item), "bytes": item.stat().st_size}
    return files


def broker_command(ipc: Path, repo: str) -> list[str]:
    """Every case owns one request except idle, and --once is safe for both."""
    return [sys.executable, str(BROKER), "--ipc", str(ipc),
            "--repo", repo, "--once"]


def run_case(name: str, fake: Path, *, child_exit: int = 0,
             child_sleep: float = 0, broker_timeout: float = 2,
             missing: bool = False, malformed: bool = False,
             idle: bool = False, queued: bool = False) -> dict:
    case_dir = OUT / "cases" / name
    ipc = case_dir / "ipc"
    ipc.mkdir(parents=True)
    log = case_dir / "child-calls.jsonl"
    env = os.environ.copy()
    env.update({
        "CODEX_EXE": "/tmp/missing-codex-exe" if missing else str(fake),
        "HOST_MODEL_BROKER_TIMEOUT_S": str(broker_timeout),
        "FAKE_CALL_LOG": str(log), "FAKE_EXIT": str(child_exit),
        "FAKE_SLEEP": str(child_sleep),
        "FAKE_RESPONSE": "fake-response-" + name,
    })
    repo = "/out/cases/" + name
    if malformed:
        (ipc / "00.request.json").write_text('{"request_id":', encoding="utf-8")
    elif not idle:
        requests = ["a", "z"] if queued else [name]
        for request_id in requests:
            write_json(ipc / (request_id + ".request.json"), {
                "request_id": request_id, "schema": "/repo/schema.json",
                "working": "/repo", "prompt": "prompt:" + request_id,
            })
    args = broker_command(ipc, repo)
    started = time.monotonic_ns()
    stdout = stderr = ""
    process_code = None
    external_timeout = False
    process = subprocess.Popen(args, cwd="/", env=env, text=True,
                               encoding="utf-8", errors="replace",
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        stdout, stderr = process.communicate(timeout=0.30 if idle else 5.0)
        process_code = process.returncode
    except subprocess.TimeoutExpired:
        external_timeout = True
        process.kill()
        stdout, stderr = process.communicate()
        process_code = process.returncode
    elapsed_ns = time.monotonic_ns() - started
    (case_dir / "broker.stdout.txt").write_text(stdout, encoding="utf-8")
    (case_dir / "broker.stderr.txt").write_text(stderr, encoding="utf-8")
    calls = []
    if log.exists():
        calls = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    record = {
        "name": name, "process_code": process_code,
        "external_timeout": external_timeout, "elapsed_ns": elapsed_ns,
        "stdout": stdout, "stderr": stderr, "calls": calls,
        "ipc": snapshot(ipc),
        "command": args, "child_exit_requested": child_exit,
        "child_sleep_requested": child_sleep,
    }
    write_json(case_dir / "case.json", record)
    return record


def main() -> int:
    out = OUT / "cases"
    out.mkdir(parents=True, exist_ok=True)
    fake = Path("/tmp/fake-codex")
    make_fake(fake)
    cases = [
        run_case("exit-0", fake),
        run_case("exit-23", fake, child_exit=23),
        run_case("timeout", fake, child_sleep=1, broker_timeout=0.1),
        run_case("missing-executable", fake, missing=True),
        run_case("malformed-json", fake, malformed=True),
        run_case("idle-once", fake, idle=True),
        run_case("sorted-once", fake, queued=True),
    ]
    write_json(OUT / "raw.json", {
        "allocation": "broker-fake-child-boundary-4485-20260928-02",
        "cases": cases,
        "source_sha256": digest(BROKER),
        "fake_child_sha256": digest(fake),
        "python": sys.version,
        "image_id": os.environ.get("FROZEN_IMAGE_ID"),
        "authority_granted": False,
    })
    print(json.dumps({"cases": len(cases), "raw_sha256": digest(OUT / "raw.json")},
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        (OUT / "runner.error.json").write_text(json.dumps({
            "type": type(exc).__name__, "error": repr(exc),
            "traceback": traceback.format_exc(),
        }, sort_keys=True) + "\n", encoding="utf-8")
        raise

