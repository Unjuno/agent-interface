"""One-shot raw-only audit wrapper; it never imports or invokes candidate code."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from auditor import audit_files


def main(arguments: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if arguments is None else arguments
    if len(arguments) != 2:
        print("usage: run_auditor.py CANDIDATE_JSON AUDIT_JSON", file=sys.stderr)
        return 2
    result = audit_files(arguments[0], Path(__file__).with_name("fixtures.json"))
    payload = json.dumps(result, sort_keys=True, indent=2).encode("utf-8") + bytes((10,))
    with Path(arguments[1]).open("xb") as artifact:
        artifact.write(payload)
    print(f"audit {result['status']} cases={result['cases_audited']} violations={len(result['violations'])}")
    return 0 if result["status"] == "PASS_METHOD_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
