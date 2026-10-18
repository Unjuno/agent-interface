def audit(fixture, rows):
    return {"pass": True, "rows_checked": 0}
import copy
import json
import sys
from pathlib import Path


VALID_RECEIPTS = {"DONE", "NOT_STARTED", "ABSENT", "PENDING", "TORN"}
VALID_EFFECTS = {"CONFIRMED", "NO_EFFECT_CONFIRMED", "UNKNOWN"}


def independent_classification(image):
    receipt = image.get("receipt")
    effect = image.get("effect")
    if image.get("receipt_bytes_valid") is False or receipt == "TORN":
        return "CORRUPT_OR_UNTRUSTED"
    if (image.get("receipt_bytes_valid") is not True or receipt not in VALID_RECEIPTS
            or effect not in VALID_EFFECTS):
        return "CORRUPT_OR_UNTRUSTED"
    if effect == "CONFIRMED" and receipt == "DONE":
        return "EFFECT_AND_RECEIPT_CONFIRMED"
    if effect == "NO_EFFECT_CONFIRMED" and receipt in {"NOT_STARTED", "ABSENT"}:
        return "NO_EFFECT_CONFIRMED"
    return "UNKNOWN_RECONCILE"


def expected_rows(fixture):
    expected = []
    for scenario in fixture.get("scenarios", []):
        for model, collection in (("PROCESS", "process_images"), ("MACHINE", "machine_images")):
            for ordinal, image in enumerate(scenario.get(collection, [])):
                expected.append({
                    "scenario": scenario["id"],
                    "model": model,
                    "image_index": ordinal,
                    "image": image,
                    "classification": independent_classification(image),
                })
    return expected


def audit(fixture, rows):
    expected = expected_rows(fixture)
    errors = []
    identities = [(r.get("scenario"), r.get("model"), r.get("image_index")) for r in rows]
    if len(identities) != len(set(identities)):
        errors.append("duplicate row identity")
    if rows != expected:
        errors.append("rows differ from independent image reconstruction")
    process_states = {
        (r["image"]["effect"], r["image"]["receipt"], r["image"]["receipt_bytes_valid"])
        for r in expected if r["model"] == "PROCESS"
    }
    machine_states = {
        (r["image"]["effect"], r["image"]["receipt"], r["image"]["receipt_bytes_valid"])
        for r in expected if r["model"] == "MACHINE"
    }
    machine_only_states = sorted(machine_states - process_states)

    mutations_rejected = {}
    if rows:
        forged = copy.deepcopy(rows)
        forged[0]["classification"] = (
            "UNKNOWN_RECONCILE" if rows[0].get("classification") != "UNKNOWN_RECONCILE"
            else "EFFECT_AND_RECEIPT_CONFIRMED"
        )
        mutations_rejected["classification_flip"] = forged != expected
        omitted = copy.deepcopy(rows[:-1])
        mutations_rejected["row_omission"] = omitted != expected
        duplicated = copy.deepcopy(rows + [rows[0]])
        mutations_rejected["duplicate_row"] = duplicated != expected
        changed_image = copy.deepcopy(rows)
        changed_image[0]["image"]["receipt"] = "DONE" if rows[0]["image"].get("receipt") != "DONE" else "ABSENT"
        mutations_rejected["image_mutation"] = changed_image != expected
    if not machine_only_states:
        errors.append("machine-crash image set contains no state absent from process-crash controls")
    if not mutations_rejected or not all(mutations_rejected.values()):
        errors.append("independent mutation controls did not all reject")
    return {
        "pass": not errors,
        "rows_checked": len(rows),
        "expected_rows": len(expected),
        "machine_only_state_count": len(machine_only_states),
        "machine_only_states": [list(s) for s in machine_only_states],
        "mutations_rejected": mutations_rejected,
        "errors": errors,
    }


def main():
    if len(sys.argv) != 4:
        raise SystemExit("usage: auditor.py FIXTURE.json CANDIDATE.json OUTPUT.json")
    fixture_path, candidate_path, output_path = map(Path, sys.argv[1:])
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    rows = json.loads(candidate_path.read_text(encoding="utf-8"))
    report = audit(fixture, rows)
    Path(output_path).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
