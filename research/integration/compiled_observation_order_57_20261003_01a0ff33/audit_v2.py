"""Additive raw reconciliation; preserves A01's original count-gate FAIL."""
import copy
import hashlib
import json
from pathlib import Path

from audit import check
from oracle import expected, legacy_expected, same_json

HERE = Path(__file__).resolve().parent


def main():
    pins = json.loads((HERE / "AUDIT_V2_FREEZE.json").read_bytes())
    for name, digest in pins["files"].items():
        assert hashlib.sha256((HERE / name).read_bytes()).hexdigest() == digest, name
    freeze_bytes = (HERE / "FREEZE.json").read_bytes()
    freeze = json.loads(freeze_bytes)
    for name, record in freeze["files"].items():
        assert hashlib.sha256((HERE / name).read_bytes()).hexdigest() == record["sha256"], name
    cases = json.loads((HERE / "cases.json").read_bytes())
    rows = [json.loads(line) for line in (HERE / "raw.jsonl").read_text(encoding="utf-8").splitlines()]
    freeze_hash = hashlib.sha256(freeze_bytes).hexdigest()
    result = check(rows, freeze, cases, freeze_hash)
    calculated = {}
    for source, rule in (("baseline", legacy_expected), ("candidate", expected)):
        predictions = [rule(case) for case in cases]
        calculated[source] = {
            "rows": len(cases),
            "order_rule_mismatches": sum(not same_json(prediction, expected(case))
                                          for prediction, case in zip(predictions, cases)),
            "task_succeeded": sum(prediction.get("outcome") == "TASK_SUCCEEDED"
                                  for prediction in predictions),
        }
    assert not result["errors"] and same_json(result["counts"], calculated)
    witnesses = json.loads((HERE / "CONTROLS.json").read_bytes())
    assert len(witnesses) == 8 and len({w["name"] for w in witnesses}) == 8
    for witness in witnesses:
        changed = copy.deepcopy(rows)
        index = witness["row_index"]
        assert same_json(witness["original"], rows[index])
        if witness["changed"] is None:
            changed.pop(index)
        else:
            changed[index] = witness["changed"]
        assert not same_json(changed, rows)
        assert check(changed, freeze, cases, freeze_hash)["errors"], witness["name"]
    result.update(disposition="RECONCILED_RAW_ONLY_SUPPLEMENT",
                  first_disposition="FAIL_ORDER_GUARD_ENGINEERING_SCOPED",
                  original_frozen_counts=freeze["decision"]["expected_counts"],
                  declaratively_derived_counts=calculated,
                  explanation="Each eleven-value site has FOUR type/sign-invalid values, not three; 33-12=21 baseline successes and 21-10=11 candidate successes.",
                  mutation_controls_rejected=len(witnesses),
                  candidate_replays=0, formal_allocations=0,
                  raw_sha256=hashlib.sha256((HERE / "raw.jsonl").read_bytes()).hexdigest())
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
