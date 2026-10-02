from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path


SOURCE_REL = Path("research/doom/map01_recovery_cover_matched_v2_runner_3211_diagnostic_v2.py")
SOURCE_BLOB = "f5caf71a743a563b7de046b82d44db7ebe49e829"
EXPECTED_CASES = {
    "within_bound": {"terminal_id": "fallback-within", "delay_s": 0.02, "hold_s": 0.0, "timeout_s": 1.5},
    "wrong_id": {"terminal_id": "other-terminal", "delay_s": 0.02, "hold_s": 1.2, "timeout_s": 0.6},
    "absent": {"terminal_id": None, "delay_s": 0.0, "hold_s": 0.45, "timeout_s": 0.12},
    "late_exact": {"terminal_id": "fallback-late", "delay_s": 0.25, "hold_s": 0.0, "timeout_s": 0.05},
}


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def verify_freeze(bundle_root: Path) -> dict:
    freeze_raw = (bundle_root / "FREEZE.json").read_bytes()
    freeze = json.loads(freeze_raw)
    if freeze.get("main_sha") != "bd77907946b7164e7513c3f5893f99348639e48a":
        raise ValueError("main freeze mismatch")
    for filename, expected in freeze.get("files", {}).items():
        actual = hashlib.sha256((bundle_root / filename).read_bytes()).hexdigest().upper()
        if actual != expected:
            raise ValueError(f"frozen source mismatch: {filename}")
    return freeze


def load_session_class(repo_root: Path):
    source = repo_root / SOURCE_REL
    actual = git_blob_sha1(source.read_bytes())
    if actual != SOURCE_BLOB:
        raise ValueError(f"upstream runner blob mismatch: {actual}")
    spec = importlib.util.spec_from_file_location("frozen_map01_session_wait", source)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen runner")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.JsonSession


CHILD_CODE = r'''import json,sys,time
spec=json.loads(sys.argv[1])
def emit(row):
    row=dict(row)
    row["child_emit_monotonic_ns"]=time.monotonic_ns()
    print(json.dumps(row,sort_keys=True,separators=(",",":")),flush=True)
emit({"event":"ready"})
time.sleep(spec["delay_s"])
if spec["terminal_id"] is not None:
    emit({"event":"terminal","id":spec["terminal_id"]})
time.sleep(spec["hold_s"])
'''


def run_case(session_cls, out_dir: Path, name: str, spec: dict) -> dict:
    case_dir = out_dir / name
    case_dir.mkdir(parents=True, exist_ok=False)
    expected_id = {
        "within_bound": "fallback-within",
        "wrong_id": "fallback-expected",
        "absent": "fallback-absent",
        "late_exact": "fallback-late",
    }[name]
    command = [
        sys.executable, "-B", "-c", CHILD_CODE,
        json.dumps(spec, separators=(",", ":")),
        "--out", str(case_dir / "synthetic-session.json"),
    ]
    session = session_cls(command)
    wait_start_ns = None
    wait_deadline_ns = None
    wait_end_ns = None
    wait_return = None
    wait_error = None
    try:
        session.wait(lambda row: row.get("event") == "ready", timeout=2.0)
        wait_start_ns = time.monotonic_ns()
        wait_deadline_ns = wait_start_ns + int(spec["timeout_s"] * 1_000_000_000)
        try:
            wait_return = session.wait(
                lambda row: row.get("event") == "terminal" and row.get("id") == expected_id,
                timeout=spec["timeout_s"],
            )
            wait_end_ns = time.monotonic_ns()
            disposition = "MATCHED_TERMINAL"
        except TimeoutError as exc:
            wait_end_ns = time.monotonic_ns()
            wait_error = {"type": type(exc).__name__, "message": str(exc)}
            disposition = "TIMEOUT"

        if name == "late_exact":
            session.process.wait(timeout=2.0)
        elif disposition == "TIMEOUT":
            session.terminate()
        else:
            session.process.wait(timeout=2.0)
        session._reader.join(timeout=2.0)
        if session._reader.is_alive():
            raise TimeoutError("synthetic stdout reader did not finish")
        if session.process.poll() is None:
            raise RuntimeError("synthetic child process was not reaped")
        events = list(session.events)
        trace_path = case_dir / "session-events.jsonl"
        raw = trace_path.read_bytes()
        return {
            "case": name,
            "expected_id": expected_id,
            "disposition": disposition,
            "wait_return": wait_return,
            "wait_error": wait_error,
            "wait_start_ns": wait_start_ns,
            "wait_deadline_ns": wait_deadline_ns,
            "wait_end_ns": wait_end_ns,
            "events": events,
            "child_exit_code": session.process.returncode,
            "child_reaped": session.process.poll() is not None,
            "reader_joined": not session._reader.is_alive(),
            "trace_file": f"{name}/session-events.jsonl",
            "trace_byte_count": len(raw),
            "trace_sha256": hashlib.sha256(raw).hexdigest(),
        }
    finally:
        session.terminate()


def run(out_dir: Path) -> dict:
    bundle_root = Path(__file__).resolve().parent
    repo_root = bundle_root.parents[2]
    verify_freeze(bundle_root)
    if git_blob_sha1((repo_root / SOURCE_REL).read_bytes()) != SOURCE_BLOB:
        raise ValueError("current runner source blob mismatch")
    expected_out = bundle_root / "results" / "t4-01"
    out_dir = out_dir.resolve()
    if out_dir != expected_out.resolve():
        raise ValueError(f"output path must be exactly {expected_out}")
    if out_dir.exists():
        raise FileExistsError(f"candidate output path already exists: {out_dir}")
    out_dir.mkdir(parents=True)
    session_cls = load_session_class(repo_root)
    results = [run_case(session_cls, out_dir, name, spec) for name, spec in EXPECTED_CASES.items()]
    freeze_raw = (bundle_root / "FREEZE.json").read_bytes()
    receipt = {
        "schema": "map01-terminal-wait-boundary-candidate-v1",
        "main_sha": "bd77907946b7164e7513c3f5893f99348639e48a",
        "runner_git_blob": SOURCE_BLOB,
        "freeze_sha256": hashlib.sha256(freeze_raw).hexdigest(),
        "candidate_invocations": 1,
        "synthetic_child_cases": len(results),
        "retries": 0,
        "cases": results,
    }
    (out_dir / "candidate.json").write_text(
        json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    run(parser.parse_args().out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
