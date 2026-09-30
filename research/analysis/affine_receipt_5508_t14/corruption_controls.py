#!/usr/bin/env python3
"""Mutation controls for the T14 independent auditor."""
import copy
import json
from pathlib import Path
import shutil
import tempfile

from audit import audit


def main(source):
    source = Path(source)
    lines = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line]
    bad = {"missing_worker": copy.deepcopy(lines)}
    bad["missing_worker"][1]["workers"].pop()
    forged = copy.deepcopy(lines)
    next(row for row in forged[1:] if row["case_id"] == "distinct_delivery_race")["recovery"] = "CONFIRMED_SAME_ATTEMPT"
    bad["false_distinct_confirmation"] = forged
    forged = copy.deepcopy(lines)
    forged[1]["workers"][1]["outcome"] = "INSERTED"
    bad["forged_concurrent_insert"] = forged
    results = {}
    with tempfile.TemporaryDirectory(prefix="5508-t14-controls-") as td:
        shutil.copytree(source.parent / "db", Path(td) / "db")
        for name, variant in bad.items():
            mutated = Path(td) / f"{name}.jsonl"
            mutated.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in variant), encoding="utf-8")
            results[name] = audit(mutated)
    print(json.dumps({"control_count": len(results), "all_rejected": all(x["audit"] == "FAIL" for x in results.values()),
                      "controls": results}, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    import sys
    main(sys.argv[1])
