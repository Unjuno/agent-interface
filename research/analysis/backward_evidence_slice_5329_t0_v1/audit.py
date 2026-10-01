import hashlib
import json
import sys
from pathlib import Path


raw_path = Path(sys.argv[1])
raw_bytes = raw_path.read_bytes()
doc = json.loads(raw_bytes)
errors = []
predicates = ("semantic", "authority", "lineage", "freshness", "release", "contradiction")


def independent_closure(nodes, allowed=None):
    reached, frontier = {"decision"}, ["decision"]
    while frontier:
        current = frontier.pop(0)
        for link in nodes[current].get("edges", []):
            if allowed is not None and link["kind"] not in allowed:
                continue
            target = link["to"]
            if target not in reached:
                reached.add(target)
                frontier.append(target)
    return sorted(reached)


def independent_decision(row, retained):
    if not row["graph_complete"]:
        return "UNKNOWN"
    if not set(predicates).issubset(retained):
        return "UNKNOWN"
    truth = row["ground_truth"]
    if truth["unknown_external"]:
        return "UNKNOWN"
    if not truth["freshness"]:
        return "STALE"
    if not truth["authority"]:
        return "NO_AUTHORITY"
    if not truth["lineage"]:
        return "UNATTRIBUTED"
    if not truth["release"]:
        return "UNRELEASED"
    if not truth["contradiction"]:
        return "CONTRADICTED_OR_UNCHECKED"
    if not truth["semantic"]:
        return "NO_EFFECT"
    return "PASS"


for row in doc["rows"]:
    nodes = row["nodes"]
    for key, allowed in (("full", None), ("data_slice", {"data"}), ("typed_slice", None)):
        expected_retained = sorted(nodes) if key == "full" else independent_closure(nodes, allowed)
        observed = row[key]["retained"]
        if observed != expected_retained:
            errors.append(f"{row['case_id']}:{key}:retention_mismatch")
        if key != "data_slice" and row[key]["decision"] != independent_decision(row, observed):
            errors.append(f"{row['case_id']}:{key}:decision_mismatch")
    if row["typed_slice"]["decision"] != row["oracle"]:
        errors.append(f"{row['case_id']}:typed_not_oracle")
    if row["full"]["decision"] != row["oracle"]:
        errors.append(f"{row['case_id']}:raw_not_oracle")

clean = doc["rows"][0]
if len(clean["typed_slice"]["retained"]) >= len(clean["full"]["retained"]):
    errors.append("noise_case_no_strict_reduction")
if doc["rows"][1]["data_slice"]["decision"] == doc["rows"][1]["oracle"]:
    errors.append("stale_negative_control_not_discriminating")
if doc["rows"][2]["data_slice"]["decision"] == doc["rows"][2]["oracle"]:
    errors.append("control_dependency_negative_control_not_discriminating")
if doc["rows"][3]["typed_slice"]["decision"] != "UNKNOWN":
    errors.append("unknown_external_not_fail_closed")

corruptions = []
for name, transform in (
    ("drop_freshness_from_slice", lambda x: x["rows"][0]["typed_slice"]["retained"].remove("freshness")),
    ("drop_control_edge", lambda x: x["rows"][2]["nodes"]["decision"]["edges"].pop()),
    ("forge_oracle", lambda x: x["rows"][1].update(oracle="PASS")),
    ("erase_unknown_cause_edge", lambda x: (x["rows"][3]["nodes"]["decision"]["edges"].pop(), x["rows"][3].update(graph_complete=True))),
):
    mutant = json.loads(json.dumps(doc))
    transform(mutant)
    before = len(errors)
    # Re-derive the same invariants for this mutant; each must add a discrepancy.
    row_errors = []
    for row in mutant["rows"]:
        for key, allowed in (("full", None), ("data_slice", {"data"}), ("typed_slice", None)):
            expected_retained = sorted(row["nodes"]) if key == "full" else independent_closure(row["nodes"], allowed)
            if row[key]["retained"] != expected_retained:
                row_errors.append("retention")
        if row["typed_slice"]["decision"] != row["oracle"]:
            row_errors.append("decision")
    corruptions.append({"name": name, "rejected": bool(row_errors), "signals": row_errors})
    if not row_errors:
        errors.append(f"corruption_escaped:{name}")

result = {"schema": "issue5329-backward-slice-audit-v1", "errors": errors,
          "rows": len(doc["rows"]), "corruptions": corruptions,
          "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
          "disposition": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT"}
print(json.dumps(result, sort_keys=True))
sys.exit(0 if not errors else 1)
