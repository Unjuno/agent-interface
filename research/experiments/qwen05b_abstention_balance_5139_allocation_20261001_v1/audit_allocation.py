"""Independent CPU-only wrapper: verify current-main provenance then raw audit."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiments-root", required=True)
    parser.add_argument("--allocation-dir", required=True)
    parser.add_argument("--candidate-dir", required=True)
    parser.add_argument("--data", required=True)
    parser.add_argument("--results", required=True)
    parser.add_argument("--audit-out", required=True)
    args = parser.parse_args()
    root, allocation, candidate = map(Path, (args.experiments_root, args.allocation_dir, args.candidate_dir))
    data_path, results, audit_out = map(Path, (args.data, args.results, args.audit_out))
    freeze = json.loads((allocation / "FREEZE.json").read_text(encoding="utf-8"))
    checks = []
    for entry in freeze["external_sources"]:
        path = root / entry["experiments_path"]
        actual = sha(path) if path.is_file() else None
        checks.append({"repo_path": entry["repo_path"], "expected": entry["sha256"], "actual": actual,
                       "pass": actual == entry["sha256"]})
    source_receipt = {"schema": "qwen5139-independent-source-audit-v1",
                      "current_main_sha": freeze["current_main_sha"], "checks": checks,
                      "pass": all(row["pass"] for row in checks)}
    coverage_path = allocation / "COVERAGE_SUMMARY.json"
    coverage_sha = sha(coverage_path) if coverage_path.is_file() else None
    source_receipt["coverage_summary_sha256"] = coverage_sha
    source_receipt["coverage_summary_pass"] = (
        coverage_sha == freeze["data"]["coverage_summary_sha256"] and
        json.loads(coverage_path.read_text(encoding="utf-8")).get("formal_input_sha256") ==
        freeze["data"]["formal_input_sha256"])
    source_receipt["pass"] = source_receipt["pass"] and source_receipt["coverage_summary_pass"]
    audit_out.mkdir(parents=True, exist_ok=True)
    (audit_out / "SOURCE_AUDIT.json").write_text(json.dumps(source_receipt, sort_keys=True, indent=2) + "\n",
                                                 encoding="utf-8")
    if not source_receipt["pass"]:
        raise SystemExit("STOP_CURRENT_MAIN_SOURCE_AUDIT")
    sys.path.insert(0, str(candidate))
    from audit_raw import audit
    orchestration = json.loads((results / "ORCHESTRATION.json").read_text(encoding="utf-8"))
    orchestration["out_dir"] = str(results)
    raw = {arm: json.loads((results / (arm + "-raw.json")).read_text(encoding="utf-8"))
           for arm in ("base", "imbalanced", "balanced")}
    report = audit(data_path.read_bytes(), raw, freeze, orchestration, allocation)
    (audit_out / "AUDIT.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n",
                                          encoding="utf-8")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
