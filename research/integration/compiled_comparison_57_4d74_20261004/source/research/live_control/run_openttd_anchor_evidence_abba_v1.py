"""Run the preregistered single-anchor correct/wrong ABBA."""
import json
from pathlib import Path

from anchor_evidence_contract_v1 import validate
import run_openttd_active_evidence_pair_v1 as base


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/openttd-anchor-evidence-abba-01"
base.WORKSPACE = OUT / "empty-workspace"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    plan = read(OUT / "preregistration.json")
    for name, digest in plan["sources"].items(): assert base.sha(HERE / name) == digest, name
    for condition, evidence in plan["fixed_evidence"].items():
        for key in ("result", "events", "dwell_image"):
            assert base.sha(HERE / evidence[key]) == evidence[f"{key}_sha256"], key
        assert base.sha(OUT / f"{condition}.png") == evidence["presentation_sha256"]
    rows = []
    for name in plan["execution_order"]:
        condition = plan["condition_by_call"][name]
        readiness = read(OUT / f"{condition}-readiness.json")
        model = base.model_call(
            OUT, name, plan["common_prompt"], OUT / f"{condition}.png",
            "anchor_evidence_responder_v1.txt", "anchor_evidence_contract_schema_v1.json")
        decision = validate(model["typed"], readiness)
        expected = plan["expected_op"][condition]
        rows.append({"name": name, "condition": condition, "expected_op": expected,
                     "model": model, "decision": decision,
                     "correct": model["typed"]["op"] == expected})
        base.dump(OUT / "partial-results.json", rows)
    gate = {
        "correct_anchor_accepts_two_of_two": all(row["correct"] for row in rows
                                                  if row["condition"] == "correct"),
        "wrong_anchor_expands_two_of_two": all(row["correct"] for row in rows
                                                if row["condition"] == "wrong"),
        "all_four_receipt_bound": all(row["decision"]["status"] in
                                      ("EVIDENCE_BOUND", "EXPANSION_REQUIRED") for row in rows),
    }
    gate["passed"] = all(gate.values())
    report = {"results": rows, "promotion_gate": gate,
              "reported_input_tokens": {row["name"]: row["model"]["usage"]["input_tokens"]
                                         for row in rows},
              "decision": ("RETAIN_ANCHOR_FIRST_EVIDENCE_DECISION"
                           if gate["passed"] else "HOLD_ANCHOR_FIRST_EVIDENCE_DECISION"),
              "scope": plan["scope"]}
    base.dump(OUT / "report.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
