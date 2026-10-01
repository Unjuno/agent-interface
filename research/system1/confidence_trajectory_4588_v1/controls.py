#!/usr/bin/env python3
"""Apply effective semantic/provenance mutations to copies of formal raw rows."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

from audit import audit_rows


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: controls.py RAW_JSONL")
    original = [json.loads(line) for line in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines()]
    specifications = (
        ("truth_label", lambda r: r["input"].update(truth="YIELD")),
        ("confidence_bytes", lambda r: r["input"].update(scores=[.11, .22, .33])),
        ("sample_clock", lambda r: r["input"].update(times_ms=[0, 0, 200])),
        ("history_epoch", lambda r: r["input"].update(history_status="EPOCH_MISMATCH")),
        ("intent_scope", lambda r: r["input"].update(intent_id="foreign-intent")),
        ("candidate_decision", lambda r: r["predictions"]["CURRENT_ONLY"].update(decision="YIELD")),
        ("decision_provenance", lambda r: r["predictions"]["LEVEL_PLUS_VELOCITY"].update(source="CURRENT_ONLY")),
        ("feature_provenance", lambda r: r["predictions"]["LEVEL_PLUS_VELOCITY_PLUS_ACCEL"].update(features_used=[])),
    )
    results = []
    for name, mutate in specifications:
        changed = copy.deepcopy(original)
        before = json.dumps(changed[0], sort_keys=True)
        mutate(changed[0])
        effective = before != json.dumps(changed[0], sort_keys=True)
        errors = audit_rows(changed)
        results.append({"control": name, "effective": effective, "rejected": bool(errors), "audit_error_count": len(errors)})
    accepted = sum(not row["rejected"] for row in results)
    report = {"controls": len(results), "effective_rejections": len(results) - accepted, "accepted_mutations": accepted, "results": results}
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0 if accepted == 0 and all(row["effective"] and row["rejected"] for row in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
