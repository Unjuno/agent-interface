"""Emit a candidate report for W2 lease-close binding cases."""
import argparse
import hashlib
import json
from pathlib import Path

from close_order_candidate import evaluate


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--traces", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise SystemExit("STOP_CANDIDATE_OUTPUT_EXISTS")
    raw = args.traces.read_bytes()
    document = json.loads(raw)
    cases = [{"case_id": case["case_id"], "decisions": evaluate(case["events"])}
             for case in document["cases"]]
    report = {
        "schema": "w2-lease-close-candidate-report-v1",
        "trace_sha256": hashlib.sha256(raw).hexdigest(),
        "case_count": len(cases),
        "cases": cases,
    }
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"case_count": len(cases), "report_sha256": hashlib.sha256(args.out.read_bytes()).hexdigest()}))


if __name__ == "__main__":
    main()
