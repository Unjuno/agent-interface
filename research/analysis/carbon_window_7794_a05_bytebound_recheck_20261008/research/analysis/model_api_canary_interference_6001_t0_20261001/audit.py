#!/usr/bin/env python3
"""Independent raw-event auditor for Issue #6001 T0 fixture."""
import json
import math
import sys
from collections import defaultdict

ALPHA = 0.01
MIN_SHIFT = 0.20
REPLICATES = 240


def mean(xs):
    return sum(xs) / len(xs) if xs else math.nan


def audit(path):
    groups = defaultdict(list)
    seen = set()
    errors = []
    with open(path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            try:
                row = json.loads(line)
                key = (row["policy"], row["scenario"], row["trial"])
                if key in seen:
                    errors.append(f"duplicate key line {lineno}")
                    continue
                seen.add(key)
                routes = [e for e in row["events"] if e["kind"] == "route"]
                if [e["arm"] for e in routes] != ["A", "B"]:
                    errors.append(f"route order line {lineno}")
                    continue
                if any(e["finish"] < e["start"] for e in row["events"]):
                    errors.append(f"negative duration line {lineno}")
                    continue
                if row["semantic_shift_planted"] != (row["scenario"] in ("semantic_shift", "both")):
                    errors.append(f"scenario provenance line {lineno}")
                    continue
                a, b = routes
                groups[(row["scenario"], row["policy"])].append(
                    {"delta": (b["finish"] - b["submitted"]) - (a["finish"] - a["submitted"]),
                     "b_wait": b["start"] - b["submitted"],
                     "canary": row["canary_post"]})
            except Exception as e:
                errors.append(f"parse line {lineno}: {e}")
    if errors:
        return {"verdict": "FAIL_AUDIT", "errors": errors[:20], "n_errors": len(errors)}
    expected = 4 * 4 * REPLICATES
    if len(seen) != expected:
        return {"verdict": "FAIL_AUDIT", "errors": [f"expected {expected} unique rows, got {len(seen)}"]}
    summary = {}
    for (scenario, policy), rows in sorted(groups.items()):
        summary[f"{scenario}/{policy}"] = {
            "n": len(rows), "mean_route_latency_delta_s": mean([r["delta"] for r in rows]),
            "mean_B_queue_wait_s": mean([r["b_wait"] for r in rows]),
            "post_canary_success_rate": mean([r["canary"] for r in rows]),
        }
    # The preregistered interference gate uses B queue wait: shared canary and
    # equal-cost sham must exceed both no-probe and isolated by >=5.9s.
    base = summary["interference_only/no_probe"]["mean_B_queue_wait_s"]
    iso = summary["interference_only/isolated_canary"]["mean_B_queue_wait_s"]
    shared = summary["interference_only/shared_canary"]["mean_B_queue_wait_s"]
    sham = summary["interference_only/shared_sham"]["mean_B_queue_wait_s"]
    interference = shared - base >= 5.9 and sham - base >= 5.9 and abs(shared - sham) < 0.01 and abs(iso - base) < 0.01
    # Semantic detector is a fixed threshold on post-bracket canary score. The
    # paired synthetic samples must show a >=.20 drop in shift cells and <.20
    # in null cells; this is a fixture gate, not a calibrated inferential test.
    semantic = all(summary[f"{s}/{p}"]["post_canary_success_rate"] < 0.70
                   for s in ("semantic_shift", "both") for p in POLICIES)
    null_clean = all(summary[f"null/{p}"]["post_canary_success_rate"] >= 0.70 for p in POLICIES)
    return {"verdict": "PASS_METHOD_SCOPED" if interference and semantic and null_clean else "FAIL_METHOD",
            "n_rows": len(seen), "gates": {"shared_canary_interference_detected": interference,
            "semantic_shift_detected": semantic, "stationary_null_not_flagged": null_clean},
            "summary": summary, "errors": []}


POLICIES = ("no_probe", "shared_canary", "shared_sham", "isolated_canary")

if __name__ == "__main__":
    result = audit(sys.argv[1])
    print(json.dumps(result, sort_keys=True, indent=2))
    sys.exit(0 if result["verdict"] == "PASS_METHOD_SCOPED" else 1)
