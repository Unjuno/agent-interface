#!/usr/bin/env python3
"""Verify the independent audit rejects four corrupted pilot artifacts."""
import copy
import json
from pathlib import Path
import shutil
import tempfile

from audit import audit


def main(source):
    source = Path(source)
    lines = [json.loads(x) for x in source.read_text(encoding="utf-8").splitlines() if x]
    bad = {}
    bad["missing_case"] = copy.deepcopy(lines[:-1])
    forged = copy.deepcopy(lines)
    next(r for r in forged[1:] if r["case"]["case_id"] == "wrong_target")["recovery"] = "CONFIRMED_SAME_ATTEMPT"
    bad["forged_confirmation"] = forged
    forged = copy.deepcopy(lines)
    row = next(r for r in forged[1:] if r["case"]["case_id"] == "foreign_lineage")
    row["receipt_rows"][0]["attempt_id"] = "attempt-foreign"
    bad["forged_receipt_lineage"] = forged
    forged = copy.deepcopy(lines)
    row = next(r for r in forged[1:] if r["case"]["case_id"] == "normal_valid")
    row["effect_rows"].append(copy.deepcopy(row["effect_rows"][0]))
    bad["duplicate_delivery"] = forged
    results = {}
    with tempfile.TemporaryDirectory(prefix="5508-t12-corruption-") as td:
        root = Path(td)
        shutil.copytree(source.parent / "db", root / "db")
        for name, variant in bad.items():
            trial = root / f"{name}.jsonl"
            trial.write_text("".join(json.dumps(x, sort_keys=True, separators=(",", ":")) + "\n" for x in variant), encoding="utf-8")
            results[name] = audit(trial)
    result = {"control_count": len(results), "all_rejected": all(x["audit"] == "FAIL" for x in results.values()),
              "controls": results}
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    import sys
    main(sys.argv[1])
