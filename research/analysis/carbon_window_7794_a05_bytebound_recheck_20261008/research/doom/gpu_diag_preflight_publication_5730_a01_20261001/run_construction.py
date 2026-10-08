import argparse
import hashlib
import json
from pathlib import Path
import sys

import gate


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    package = Path(__file__).resolve().parent
    freeze = json.loads(args.freeze.read_text(encoding="utf-8"))
    if freeze.get("schema") != "issue5730-freeze-v1":
        raise SystemExit("STOP_FREEZE_SCHEMA")
    for name, expected in freeze["files"].items():
        actual_path = package / name
        if not actual_path.is_file() or sha256(actual_path) != expected:
            raise SystemExit(f"STOP_FROZEN_SOURCE_MISMATCH:{name}")

    candidate = package / "synthetic_candidate.py"
    candidate_sha = freeze["files"]["synthetic_candidate.py"]
    result = gate.execute(
        gpu_snapshot="0 %, 0 MiB",
        compute_apps=None,
        gpu_query_exit=0,
        apps_query_exit=0,
        source_expected=candidate_sha,
        source_path=candidate,
        output_dir=args.output,
        argv=[sys.executable, "-B", str(candidate)],
        runner=gate.subprocess_runner,
    )
    print(json.dumps({
        "status": result.status,
        "scientific_result": result.scientific_result,
        "candidate_invocations": result.candidate_invocations,
        "audited": result.audited,
        "raw_sha256": result.raw_sha256,
        "audit_errors": list(result.audit_errors),
        "main_sha": freeze["main_sha"],
    }, sort_keys=True, separators=(",", ":")))
    return 0 if result.status == "PASS_CONSTRUCTION_ONLY" and result.audited else 1


if __name__ == "__main__":
    raise SystemExit(main())

