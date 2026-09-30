#!/usr/bin/env python3
"""Check the T15 auditor rejects forged pre-commit recovery evidence."""
import copy
import json
from pathlib import Path
import shutil
import tempfile

from audit import audit


def main(source):
    source = Path(source)
    lines = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line]
    bad = {}
    forged = copy.deepcopy(lines)
    forged[1]["recovery"] = "CONFIRMED_SAME_ATTEMPT"
    forged[0]["decision"] = "PASS"
    bad["forged_success"] = forged
    forged = copy.deepcopy(lines)
    forged[1]["child_exit"] = 0
    bad["forged_child_exit"] = forged
    results = {}
    with tempfile.TemporaryDirectory(prefix="5508-t15-controls-") as td:
        for name, variant in bad.items():
            root = Path(td) / name
            root.mkdir()
            shutil.copy2(source.parent / "receipt.sqlite", root / "receipt.sqlite")
            shutil.copy2(source.parent / "sink.sqlite", root / "sink.sqlite")
            mutated = root / "result.jsonl"
            mutated.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in variant), encoding="utf-8")
            results[name] = audit(mutated)
    print(json.dumps({"control_count": len(results), "all_rejected": all(x["audit"] == "FAIL" for x in results.values()),
                      "controls": results}, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    import sys
    main(sys.argv[1])
