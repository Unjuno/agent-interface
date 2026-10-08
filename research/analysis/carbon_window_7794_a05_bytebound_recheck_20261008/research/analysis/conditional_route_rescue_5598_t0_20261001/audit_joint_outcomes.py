"""Read-only paired-route summary for retained synthetic #5424 inputs.

This is a post-hoc descriptive analysis, not a formal experiment or a GUI-route
test. It never reads policy outcomes or modifies the input stream.
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path


SEVERE = {"severe", "catastrophic"}


def summarize(path: Path) -> dict:
    counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    digest = hashlib.sha256()
    total = 0
    with path.open("rb") as stream:
        for raw in stream:
            digest.update(raw)
            if not raw.strip():
                continue
            row = json.loads(raw)
            a = row["primary"]["route-a"]
            b = row["primary"]["route-b"]
            group = counts[row["regime"]]
            group["n"] += 1
            group["b_ok"] += b == "ok"
            if a != "ok":
                group["a_non_ok"] += 1
                group["b_ok_given_a_non_ok"] += b == "ok"
                group["b_severe_given_a_non_ok"] += b in SEVERE
            if a in SEVERE:
                group["a_severe"] += 1
                group["b_ok_given_a_severe"] += b == "ok"
            if row.get("incident") is not None:
                group["incident_rows"] += 1
                if a != "ok":
                    group["incident_a_non_ok"] += 1
                    group["incident_b_ok_given_a_non_ok"] += b == "ok"
                    group["incident_b_severe_given_a_non_ok"] += b in SEVERE
            total += 1

    output = {"rows": total, "inputs_sha256": digest.hexdigest(), "regimes": {}}
    for regime, values in sorted(counts.items()):
        item = dict(values)
        a_n = item.get("a_non_ok", 0)
        inc_n = item.get("incident_a_non_ok", 0)
        item["p_b_ok_marginal"] = item.get("b_ok", 0) / item["n"]
        item["p_b_ok_given_a_non_ok"] = (
            item.get("b_ok_given_a_non_ok", 0) / a_n if a_n else None
        )
        item["p_b_severe_given_a_non_ok"] = (
            item.get("b_severe_given_a_non_ok", 0) / a_n if a_n else None
        )
        item["p_b_ok_given_a_severe"] = (
            item.get("b_ok_given_a_severe", 0) / item.get("a_severe", 0)
            if item.get("a_severe", 0) else None
        )
        item["p_b_ok_given_a_non_ok_and_incident"] = (
            item.get("incident_b_ok_given_a_non_ok", 0) / inc_n if inc_n else None
        )
        item["p_b_severe_given_a_non_ok_and_incident"] = (
            item.get("incident_b_severe_given_a_non_ok", 0) / inc_n if inc_n else None
        )
        output["regimes"][regime] = item
    return output


if __name__ == "__main__":
    if len(sys.argv) not in (2, 4) or (len(sys.argv) == 4 and sys.argv[2] != "--out"):
        raise SystemExit("usage: python audit_joint_outcomes.py inputs.jsonl [--out RESULT.json]")
    rendered = json.dumps(summarize(Path(sys.argv[1])), sort_keys=True, indent=2) + "\n"
    if len(sys.argv) == 4:
        Path(sys.argv[3]).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")

