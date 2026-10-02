"""CLI entry point for the separate raw-only feedback-necessity checker."""
import argparse
import json
from pathlib import Path

from feedback_necessity import audit_result


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    cases = json.loads(args.cases.read_text(encoding="utf-8"))["cases"]
    candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
    audit = audit_result(cases, candidate)
    args.out.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": audit["status"], "errors": audit["errors"]}))
    return 0 if audit["status"] == "PASS_RAW_AUDIT" else 2


if __name__ == "__main__":
    raise SystemExit(main())
