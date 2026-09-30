#!/usr/bin/env python3
"""Mutation controls for the frozen T13 independent auditor."""
import copy
import json
from pathlib import Path
import shutil
import tempfile

from audit import audit


def main(source):
    source = Path(source)
    rows = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line]
    bad = {"missing_case": copy.deepcopy(rows[:-1])}
    forged = copy.deepcopy(rows)
    next(row for row in forged[1:] if row["case_id"] == "conflicting_payload")["recovery"] = "CONFIRMED_SAME_ATTEMPT"
    bad["forged_conflict_confirmation"] = forged
    forged = copy.deepcopy(rows)
    next(row for row in forged[1:] if row["case_id"] == "out_of_order")["sink_rows"] = []
    bad["erased_out_of_order_effects"] = forged
    forged = copy.deepcopy(rows)
    next(row for row in forged[1:] if row["case_id"] == "exact_duplicate")["calls"].pop()
    bad["erased_duplicate_call"] = forged
    results = {}
    with tempfile.TemporaryDirectory(prefix="5508-t13-controls-") as td:
        shutil.copytree(source.parent / "db", Path(td) / "db")
        for name, variant in bad.items():
            candidate = Path(td) / f"{name}.jsonl"
            candidate.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in variant), encoding="utf-8")
            results[name] = audit(candidate)
    print(json.dumps({"control_count": len(results), "all_rejected": all(r["audit"] == "FAIL" for r in results.values()),
                      "controls": results}, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    import sys
    main(sys.argv[1])
