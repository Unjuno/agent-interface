#!/usr/bin/env python3
"""Exercise independent auditor rejection on four isolated corrupted copies."""
import copy
import json
import tempfile
from pathlib import Path

from audit import audit


def main(source):
    original = [json.loads(line) for line in Path(source).read_text(encoding="utf-8").splitlines() if line]
    controls = {}
    # Missing factorial case.
    controls["missing_case"] = original[:120] + original[121:]
    # Forged an unsafe result into a previously safe trace.
    c = copy.deepcopy(original)
    target = next(x for x in c[1:] if x["case"]["action_class"] == "one_shot")
    row = next(p for p in target["policies"] if p["policy"] == "ACTION_CLASS_LEVEL")
    row["unsafe_one_shot"] = True
    controls["forged_safety_flag"] = c
    # Rewrite one emitted ACK's attempt epoch while preserving the case descriptor.
    c = copy.deepcopy(original)
    target = next(x for x in c[1:] if x["ack_messages"])
    target["ack_messages"][0]["attempt"] = 0
    controls["forged_ack_epoch"] = c
    # Alter the summary liveness denominator.
    c = copy.deepcopy(original)
    c[0]["decision"]["clean_liveness_passes"] += 1
    controls["forged_liveness_summary"] = c
    results = {}
    with tempfile.TemporaryDirectory(prefix="5441-t4-controls-") as td:
        for name, rows in controls.items():
            path = Path(td) / f"{name}.jsonl"
            path.write_text("".join(json.dumps(x, sort_keys=True) + "\n" for x in rows), encoding="utf-8")
            results[name] = audit(path)
    print(json.dumps({"controls": results,
                      "all_rejected": all(v["audit"] == "FAIL" for v in results.values()),
                      "control_count": len(results)}, sort_keys=True))


if __name__ == "__main__":
    import sys
    main(sys.argv[1])
