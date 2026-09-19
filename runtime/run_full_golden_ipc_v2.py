"""Corrected, first-stop-retaining wrapper for the golden IPC allocation."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import traceback


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_report(out: Path, report: dict) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--prereg", type=Path, default=None)
    parser.add_argument("--seed", type=int, default=991029)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    prereg_path = args.prereg or root / "research" / "analysis" / "full_golden_ipc_2758_v2" / "preregistration.json"
    report = {
        "schema": "agent_interface_docker_host_ipc_live_v2",
        "issue": 2758, "seed": args.seed, "status": "NOT_STARTED",
        "first_terminal_stop": None, "authority_granted": False, "retry_count": 0,
        "accounting": {"model_calls": 0, "failed_calls": 0, "ipc_timeouts": 0,
                       "input_tokens": 0, "output_tokens": 0, "reasoning_tokens": 0,
                       "images": 0, "local_observations": 0, "effect_receipts": 0,
                       "release_receipts": 0, "cleanup": "NOT_STARTED"},
    }
    try:
        prereg = json.loads(prereg_path.read_text(encoding="utf-8"))
        mismatches = []
        for relative, expected in prereg["source_sha256"].items():
            actual_path = root / relative
            if not actual_path.is_file():
                mismatches.append({"path": relative, "reason": "missing"})
            else:
                actual = sha256(actual_path)
                if actual != expected.lower():
                    mismatches.append({"path": relative, "reason": "sha256_mismatch",
                                       "expected": expected, "actual": actual})
        if mismatches:
            report.update(status="STOP_SOURCE_HASH_MISMATCH",
                          first_terminal_stop={"kind": "source_hash_mismatch", "details": mismatches})
            write_report(args.out, report)
            return 1
        research = root / "research" / "live_control"
        sys.path.insert(0, str(research))
        import run_full_golden_ipc_v1 as legacy
        report["status"] = "RUNNING"
        report["legacy_runner"] = "runtime/run_full_golden_ipc_v1.py"
        # Isolate legacy argparse so v2-only flags cannot escape the boundary.
        old_argv = sys.argv
        try:
            sys.argv = [old_argv[0], "--out", str(args.out), "--seed", str(args.seed)]
            legacy.main()
        finally:
            sys.argv = old_argv
        report.update(status="COMPLETED", first_terminal_stop=None)
        write_report(args.out, report)
        return 0
    except BaseException as exc:
        report.update(status="STOP_EXCEPTION",
                      first_terminal_stop={"kind": "runtime_exception",
                                           "error_class": type(exc).__name__,
                                           "error": str(exc),
                                           "traceback": traceback.format_exc()[-4000:]})
        report["accounting"]["cleanup"] = "UNKNOWN"
        write_report(args.out, report)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
