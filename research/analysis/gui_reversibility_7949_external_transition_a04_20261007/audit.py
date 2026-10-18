"""Independent replay/oracle for frozen A04 raw output; candidate not imported."""
import hashlib
import json
from itertools import product
from pathlib import Path

ROOT = Path(__file__).parent
model = json.loads((ROOT / "model.json").read_text(encoding="utf-8"))
raw_bytes = (ROOT / "results/candidate.raw.json").read_bytes()
raw = json.loads(raw_bytes)
assert raw["run_id"] == model["run_id"]
rows = {r["id"]: r for r in raw["cases"]}
assert list(rows) == [c["id"] for c in model["cases"]]
errors = []

for case in model["cases"]:
    row = rows[case["id"]]
    if not case["coverage_complete"]:
        if row.get("label") != "UNKNOWN_EVENT_CHAIN":
            errors.append("coverage/gap case accepted")
        continue
    state = case["events"][0]["before"] if case["events"] else case["start"]
    rev = case["base_revision"]
    good = True
    for i, event in enumerate(case["events"], start=1):
        if event["seq"] != i or event["revision"] != rev + 1 or event["before"] != state:
            good = False
            break
        state, rev = event["after"], event["revision"]
    if not good or state != case["start"] or rev != case["snapshot_revision"]:
        errors.append(case["id"] + " raw history does not reconcile")
        continue
    if case["certificate_revision"] != case["snapshot_revision"]:
        if row.get("stale", {}).get("label") != "UNKNOWN_STALE_CERTIFICATE":
            errors.append("stale certificate was accepted")
        refreshed_target = case["target"]
        start = state
        ops = case["recovery"]
        words = [seq for n in range(model["horizon"] + 1) for seq in product(ops, repeat=n)]
        found = []
        for seq in words:
            final = start
            for action in seq:
                final = ops[action].get(final, final)
            if final == refreshed_target:
                found.append((seq, final))
        refreshed = row.get("refreshed", {})
        if not found or refreshed.get("label") != "UNIVERSALLY_UNIFORM" or refreshed.get("final") != refreshed_target:
            errors.append("fresh certificate disagrees with exhaustive recovery oracle")
        if refreshed.get("final", "")[1:2] != "1" or case["target"][1:2] != "1":
            errors.append("external writer bit was not preserved")
    else:
        ops = case["recovery"]
        found = False
        for n in range(model["horizon"] + 1):
            for seq in product(ops, repeat=n):
                final = state
                for action in seq:
                    final = ops[action].get(final, final)
                found |= final == case["target"]
        if not found or row.get("label") != "UNIVERSALLY_UNIFORM" or row.get("final") != case["target"]:
            errors.append("baseline disagrees with exhaustive recovery oracle")

mutations = []
for name, predicate in (
    ("accept_stale", lambda data: data["cases"][1]["stale"].update(label="UNIVERSALLY_UNIFORM")),
    ("erase_external_bit", lambda data: data["cases"][1]["refreshed"].update(final="000")),
    ("accept_gap", lambda data: data["cases"][2].update(label="UNIVERSALLY_UNIFORM")),
):
    altered = json.loads(raw_bytes)
    predicate(altered)
    altered_rows = {r["id"]: r for r in altered["cases"]}
    rejected = (altered_rows["stale_then_refreshed"].get("stale", {}).get("label") != "UNKNOWN_STALE_CERTIFICATE"
                or altered_rows["stale_then_refreshed"].get("refreshed", {}).get("final") != "010"
                or altered_rows["journal_gap"].get("label") != "UNKNOWN_EVENT_CHAIN")
    assert rejected, name
    mutations.append(name)

assert not errors, errors
audit = {"run_id": raw["run_id"], "disposition": "PASS_EXTERNAL_TRANSITION_SCOPE",
         "case_count": len(rows), "oracle_errors": errors,
         "mutation_rejected_count": len(mutations), "mutations_rejected": mutations,
         "candidate_sha256": hashlib.sha256(raw_bytes).hexdigest()}
(ROOT / "results/audit.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(json.dumps(audit, sort_keys=True, indent=2))
