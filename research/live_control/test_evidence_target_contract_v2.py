"""Exercise positive and abstention authority using retained live evidence."""
import copy
import json
from pathlib import Path

from evidence_target_contract_v2 import validate

HERE = Path(__file__).resolve().parent


def main():
    openttd = json.loads((HERE / "results/openttd-wrong-anchor-recovery-live-02/report.json").read_text())["result"]["expanded_readiness"]
    mindustry_report = json.loads((HERE.parent / "benchmark_discovery/results/mindustry-single-tile-matched-01/report.json").read_text())
    positive_receipt = openttd["receipts"][4]
    positive = {"op": "target_reference", "receipt_index": 5,
        "point_space": "source_observation_pixels",
        "points": [{"x": positive_receipt["point"][0], "y": positive_receipt["point"][1]}],
        "motion_model": "surface_origin_translation", "evidence_kind": "persistent_hover_tooltip",
        "diagnostic_reason": "matched"}
    negatives = [{"op": "needs_decision", "receipt_index": 0,
        "point_space": "not_applicable", "points": [], "motion_model": "not_applicable",
        "evidence_kind": "persistent_hover_tooltip", "diagnostic_reason": reason}
        for reason in ("no_match_in_observed_set", "ambiguous_evidence", "unavailable_evidence", "search_budget_exhausted")]
    selected = validate(positive, openttd)
    stopped = [validate(value, openttd) for value in negatives]
    assert selected["authority_class"] == "TARGET_REFERENCE_ONLY" and selected["point"] == positive_receipt["point"]
    assert all(value["authority_class"] == "NO_TARGET_AUTHORITY" and value["point"] is None for value in stopped)
    invalid = []
    for name, mutate in (
        ("negative_point", lambda value: value.update(points=[{"x": 1, "y": 2}])),
        ("negative_receipt", lambda value: value.update(receipt_index=1)),
        ("positive_wrong_point", lambda value: value["points"][0].update(x=value["points"][0]["x"] + 1)),
        ("positive_zero_receipt", lambda value: value.update(receipt_index=0))):
        value = copy.deepcopy(negatives[0] if name.startswith("negative") else positive)
        mutate(value)
        try: validate(value, openttd)
        except ValueError: invalid.append(name)
    assert invalid == ["negative_point", "negative_receipt", "positive_wrong_point", "positive_zero_receipt"]
    mindustry = {name: row["result"]["world_decision"] for name, row in mindustry_report["reports"].items()}
    operational = {name: ("TARGET_REFERENCE_ONLY" if value["status"] == "EVIDENCE_BOUND" else "NO_TARGET_AUTHORITY")
                   for name, value in mindustry.items()}
    assert operational == {"positive": "TARGET_REFERENCE_ONLY", "no-match": "NO_TARGET_AUTHORITY", "unreadable": "NO_TARGET_AUTHORITY"}
    print(json.dumps({"passed": True, "openttd_receipts": len(openttd["receipts"]),
        "positive_authority": selected["authority_class"],
        "negative_authorities": [value["authority_class"] for value in stopped],
        "invalid_controls": invalid, "mindustry_operational_classes": operational,
        "mindustry_preserved_diagnostics": {name: value.get("reason", "matched") for name, value in mindustry.items()}}, indent=2))


if __name__ == "__main__": main()
