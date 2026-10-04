"""Independent raw-only auditor for the A04 native-suite paired run."""
from __future__ import annotations

import hashlib
import json
import re
import statistics
import sys
from pathlib import Path

EXPECTED_RUNNER = "6ea771ce3802a1d23eb98369b1dac80e153639d0e5c9c007ccab2f24d816e27d"
EXPECTED_ORDER = ((1, "native"), (1, "wslc"), (2, "wslc"),
                  (2, "native"), (3, "native"), (3, "wslc"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_test_count(path: Path) -> int:
    data = path.read_bytes()
    match = re.findall(rb"Ran ([0-9]+) tests? in [0-9.]+s", data)
    if len(match) != 1 or not re.search(rb"\nOK(?:\s|\(|$)", data):
        raise ValueError(f"missing unique unittest PASS summary: {path}")
    return int(match[0])


def verify(formal: Path) -> dict:
    events = [json.loads(line) for line in (formal / "events.jsonl").read_text(encoding="utf-8").splitlines() if line]
    source = [e for e in events if e.get("type") == "source_gate"]
    runs = [e for e in events if e.get("type") == "candidate"]
    expected = [{"pair": pair, "arm": arm} for pair, arm in EXPECTED_ORDER]
    observed = [{"pair": e["pair"], "arm": e["arm"]} for e in runs]
    errors: list[str] = []
    if len(source) != 1 or not source[0].get("passed"):
        errors.append("source gate absent or failed")
    if observed != expected:
        errors.append(f"candidate sequence mismatch: {observed}")
    totals: dict[str, list[float]] = {"native": [], "wslc": []}
    suite_counts: dict[str, list[int]] = {"native": [], "wslc": []}
    runner_hashes = set()
    per_run = []
    for event in runs:
        pair, arm = event["pair"], event["arm"]
        run_dir = formal / f"pair-{pair:02d}" / arm
        receipt = event["receipt"]
        for stream in ("stdout", "stderr"):
            p = run_dir / receipt[f"{stream}_path"]
            if not p.is_file() or sha(p) != receipt[f"{stream}_sha256"]:
                errors.append(f"launcher {stream} hash mismatch: {pair}/{arm}")
        if receipt["exit_code"] != 0:
            errors.append(f"launcher exit {receipt['exit_code']}: {pair}/{arm}")
        result_path = run_dir / "results" / "result.json"
        if not result_path.is_file():
            errors.append(f"missing result.json: {pair}/{arm}")
            continue
        result = json.loads(result_path.read_text(encoding="utf-8"))
        runner_hashes.add(result.get("runner_sha256"))
        suites = result.get("suites", [])
        if result.get("status") != "PASS" or [s.get("suite") for s in suites] != ["protocol", "harness"]:
            errors.append(f"suite result/status mismatch: {pair}/{arm}")
        counts = []
        for suite in suites:
            if suite.get("returncode") != 0:
                errors.append(f"suite nonzero: {pair}/{arm}/{suite.get('suite')}")
            for stream, detail in suite.get("logs", {}).items():
                p = run_dir / "results" / detail.get("file", "")
                if not p.is_file() or sha(p) != detail.get("sha256"):
                    errors.append(f"suite log hash mismatch: {pair}/{arm}/{suite.get('suite')}/{stream}")
            stderr = run_dir / "results" / suite["logs"]["stderr"]["file"]
            try:
                counts.append(parse_test_count(stderr))
            except (OSError, ValueError) as error:
                errors.append(str(error))
        if len(counts) == 2:
            suite_counts[arm].append(sum(counts))
            per_run.append({"pair": pair, "arm": arm, "protocol_tests": counts[0], "harness_tests": counts[1],
                            "total_tests": sum(counts), "runner_sha256": result.get("runner_sha256"),
                            "suite_seconds": {s["suite"]: s["duration_ns"] / 1e9 for s in suites}})
        totals[arm].append(float(receipt["elapsed_seconds"]))
    if runner_hashes != {EXPECTED_RUNNER}:
        errors.append(f"runner hash differs from frozen source: {sorted(str(x) for x in runner_hashes)}")
    if len(suite_counts["native"]) != 3 or len(suite_counts["wslc"]) != 3:
        errors.append("not all six complete suite totals exist")
    elif len(set(suite_counts["native"] + suite_counts["wslc"])) != 1:
        errors.append(f"test count differs across runs: {suite_counts}")
    if len(totals["native"]) != 3 or len(totals["wslc"]) != 3:
        errors.append("candidate invocation counts are incomplete")
    if not errors:
        native_median, wslc_median = statistics.median(totals["native"]), statistics.median(totals["wslc"])
        status = "PASS_COST_SCOPED" if native_median <= .9 * wslc_median else "PASS_PORTABILITY_ONLY"
        result = {"status": status, "allocation": "6389-wsl2-vs-wslc-native-suite-a04-20261004",
                  "native_seconds": totals["native"], "wslc_seconds": totals["wslc"],
                  "native_median_seconds": native_median, "wslc_median_seconds": wslc_median,
                  "native_relative_reduction": (wslc_median - native_median) / wslc_median,
                  "candidate_count_per_arm": 3, "retry_count": 0, "runs": per_run,
                  "runner_sha256": EXPECTED_RUNNER, "test_counts_by_arm": suite_counts,
                  "errors": []}
    else:
        result = {"status": "FAIL_INDEPENDENT_AUDIT", "retry_count": 0, "errors": errors,
                  "runs": per_run, "candidate_order": observed}
    result_path = formal / "audit.json"
    with result_path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write("\n")
    return result


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: audit.py FORMAL_OUTPUT_DIRECTORY")
    outcome = verify(Path(sys.argv[1]).resolve())
    print(json.dumps(outcome, sort_keys=True))
    raise SystemExit(0 if outcome["status"].startswith("PASS_") else 1)
