from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path


EXPECTED_SOURCE_BLOB = "f5caf71a743a563b7de046b82d44db7ebe49e829"
SOURCE_REL = Path("research/doom/map01_recovery_cover_matched_v2_runner_3211_diagnostic_v2.py")


def git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def probe_rows() -> list[dict]:
    return [
        {"event": "probe", "index": 1, "text": "embedded\nvalue"},
        {"event": "terminal", "id": "synthetic-terminal"},
    ]


def run(out_dir: Path) -> dict:
    root = Path(__file__).resolve().parents[3]
    expected_out = Path(__file__).resolve().parent / "results" / "t2-01"
    out_dir = out_dir.resolve()
    if out_dir != expected_out.resolve():
        raise ValueError(f"output path must be exactly {expected_out}")
    source_path = root / SOURCE_REL
    source_bytes = source_path.read_bytes()
    source_blob = git_blob_sha1(source_bytes)
    if source_blob != EXPECTED_SOURCE_BLOB:
        raise RuntimeError(f"source blob mismatch: {source_blob}")
    if out_dir.exists():
        raise FileExistsError(f"output path must not exist: {out_dir}")
    out_dir.mkdir(parents=True)

    spec = importlib.util.spec_from_file_location("frozen_terminal_sync_runner", source_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen JsonSession source")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    rows = probe_rows()
    payload = json.dumps(rows, separators=(",", ":"))
    child_code = (
        "import json,sys\n"
        "for row in json.loads(sys.argv[1]):\n"
        " print(json.dumps(row,sort_keys=True,separators=(',',':')))\n"
    )
    command = [
        sys.executable,
        "-c",
        child_code,
        payload,
        "--out",
        str(out_dir / "session.json"),
    ]
    session = module.JsonSession(command)
    return_code = session.process.wait(timeout=5)
    session._reader.join(timeout=5)
    if session._reader.is_alive():
        raise TimeoutError("synthetic stdout reader did not finish")

    trace_path = out_dir / "session-events.jsonl"
    raw = trace_path.read_bytes()
    receipt = {
        "schema": "map01-terminal-sync-writer-reproduction-candidate-v1",
        "source_git_blob": source_blob,
        "child_exit_code": return_code,
        "memory_events": session.events,
        "memory_event_count": len(session.events),
        "trace_member": str(trace_path.relative_to(root)).replace("\\", "/"),
        "trace_byte_count": len(raw),
        "trace_sha256": hashlib.sha256(raw).hexdigest(),
    }
    (out_dir / "candidate.json").write_text(
        json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    run(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
