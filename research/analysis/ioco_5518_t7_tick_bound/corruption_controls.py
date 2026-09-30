#!/usr/bin/env python3
"""Mutation controls for the independent T7 I/O conformance auditor."""
import copy
import json
from pathlib import Path
import sys
import tempfile

from audit import audit


def main(source):
    source = Path(source)
    lines = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line]
    bad = {}
    forged = copy.deepcopy(lines)
    row = next(x for x in forged[1:] if x["case_id"] == "quiescent_after_deadline")
    row["conformant"] = True
    row["counterexample_index"] = None
    bad["over_deadline_quiescence_accepted"] = forged
    forged = copy.deepcopy(lines)
    next(x for x in forged[1:] if x["case_id"] == "explicit_unknown_after_deadline")["events"][-1]["label"] = "QUIESCENT"
    bad["unknown_collapsed_to_quiescence"] = forged
    forged = copy.deepcopy(lines[:-1])
    bad["missing_case"] = forged
    results = {}
    with tempfile.TemporaryDirectory(prefix="5518-t7-controls-") as td:
        for name, variant in bad.items():
            path = Path(td) / f"{name}.jsonl"
            path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in variant), encoding="utf-8")
            results[name] = audit(path)
    print(json.dumps({"control_count": len(results), "all_rejected": all(x["audit"] == "FAIL" for x in results.values()),
                      "controls": results}, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main(sys.argv[1])
