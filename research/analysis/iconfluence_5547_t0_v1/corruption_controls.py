"""Independent auditor corruption controls; operates only on copied raw rows."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from auditor import OPS, safe_oracle, state_for


def reject(rows: list[dict], mutation: str) -> bool:
    changed = copy.deepcopy(rows)
    if mutation == "mislabel_coordination_as_safe":
        target = next(r for r in changed if r["op_a"] == "RESERVE_QUOTA" and r["op_b"] == "RESERVE_QUOTA")
        target["label_b"] = "monotone_safe"
    elif mutation == "flip_invariant_verdict":
        changed[0]["invariant"] = not changed[0]["invariant"]
    elif mutation == "drop_pair":
        changed.pop()
    elif mutation == "forge_safe_join":
        target = next(r for r in changed if r["op_a"] == "REFRESH_EPOCH" and r["op_b"] == "COMMIT_EFFECT")
        target["joined"]["effect_committed"] = False
        target["invariant"] = True
    # Rejection is independently determined by the frozen contract, not a call to auditor.main.
    expected_rows = sum(len(v) for v in OPS.values()) ** 2
    if len(changed) != expected_rows:
        return True
    for row in changed:
        labels = {"ADD_EVIDENCE": "monotone_safe", "REVOKE_CLAIM": "monotone_safe",
                  "RECORD_IDEMPOTENT_RECEIPT": "monotone_safe", "REFRESH_EPOCH": "coordination_required",
                  "RESERVE_QUOTA": "coordination_required", "COMMIT_EFFECT": "coordination_required"}
        if row.get("label_a") != labels[row["op_a"]] or row.get("label_b") != labels[row["op_b"]]:
            return True
        a = state_for(row["op_a"], row["value_a"])
        b = state_for(row["op_b"], row["value_b"])
        expected = safe_oracle({
            "evidence": a["evidence"] | b["evidence"],
            "admitted_claims": a["admitted_claims"] | b["admitted_claims"],
            "revoked_claims": a["revoked_claims"] | b["revoked_claims"],
            "authority_epoch": max(a["authority_epoch"], b["authority_epoch"]),
            "quota_reservations": a["quota_reservations"] | b["quota_reservations"],
            "effect_committed": a["effect_committed"] or b["effect_committed"],
        })
        if row.get("invariant") is not expected:
            return True
    return False


def classification_mutation_rejected(raw: dict) -> bool:
    altered = copy.deepcopy(raw)
    altered["operation_labels"]["RESERVE_QUOTA"] = "monotone_safe"
    for row in altered["rows"]:
        if row["op_a"] == "RESERVE_QUOTA":
            row["label_a"] = "monotone_safe"
        if row["op_b"] == "RESERVE_QUOTA":
            row["label_b"] = "monotone_safe"
    labels = {"ADD_EVIDENCE": "monotone_safe", "REVOKE_CLAIM": "monotone_safe",
              "RECORD_IDEMPOTENT_RECEIPT": "monotone_safe", "REFRESH_EPOCH": "coordination_required",
              "RESERVE_QUOTA": "coordination_required", "COMMIT_EFFECT": "coordination_required"}
    return (altered["operation_labels"] != labels or
            any(row["label_a"] != labels[row["op_a"]] or row["label_b"] != labels[row["op_b"]]
                for row in altered["rows"]))


def main() -> None:
    raw = json.loads(Path("/out/candidate.json").read_text(encoding="utf-8"))
    controls = ["mislabel_coordination_as_safe", "flip_invariant_verdict", "drop_pair", "forge_safe_join", "alter_operation_classification"]
    results = {name: reject(raw["rows"], name) for name in controls if name != "alter_operation_classification"}
    results["alter_operation_classification"] = classification_mutation_rejected(raw)
    out = {"kind": "corruption_controls", "results": results,
           "passed": sum(results.values()), "total": len(results),
           "decision": "PASS" if all(results.values()) else "FAIL"}
    Path("/out/controls.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, sort_keys=True))
    if out["decision"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
