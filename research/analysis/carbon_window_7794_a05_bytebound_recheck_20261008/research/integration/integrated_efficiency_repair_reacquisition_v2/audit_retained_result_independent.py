"""Independent arithmetic/provenance audit for the retained v1 result.

This is not a fresh experiment. It intentionally uses only the standard library
and reconstructs values from the committed fixture/result JSON bytes.
"""

import json
from decimal import Decimal, ROUND_HALF_EVEN
from fractions import Fraction
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
V1 = ROOT / "integrated_efficiency_repair_reacquisition_v1"
fixture = json.loads((V1 / "fixture.json").read_bytes())
result = json.loads((V1 / "RESULT.json").read_bytes())

assert fixture["schema"] == "integrated_efficiency_repair_reacquisition_fixture_v1"
assert result["schema"] == "integrated_efficiency_repair_reacquisition_result_v1"
assert fixture["task"] == result["task"] == (
    "INTEGRATED-EFFICIENCY-REPAIR-REACQUISITION-20260917-001"
)
assert fixture["source"]["git_blob"] == result["source_git_blob"]
assert result["formal_invocation"] == 1
assert result["formal_reruns"] == 0
assert result["decision"] == "PASS_REPAIR_REACQUISITION_ACCOUNTING_SCOPED"
assert result["primary_comparator"] == fixture["primary_comparator"]

repair = fixture["repair"]
reacquisition = fixture["matched_reacquisition"]
assert repair["task"] == reacquisition["task"] == 4
assert repair["layout"] == reacquisition["layout"] == "B"
assert result["primary_comparator"] == {
    "numerator_id": "persistent.task4.layout_B.repair",
    "denominator_id": "ephemeral.task4.layout_B.cold_reacquisition",
}

field_map = {
    "durable_calls": "durable_calls",
    "input_tokens": "input_tokens",
    "local_observations": "local_observations",
    "model_visible_images": "model_visible_images",
    "output_tokens": "output_tokens",
    "planner_generations": "planner_generations",
    "reasoning_output_tokens": "reasoning_output_tokens",
}
checked = []


def verify_ratio(name, numerator, denominator):
    row = result["ratios"][name]
    assert row["numerator"] == numerator, (name, "numerator")
    assert row["denominator"] == denominator, (name, "denominator")
    assert row["difference"] == numerator - denominator, (name, "difference")
    assert Fraction(row["ratio_fraction"]) == Fraction(numerator, denominator), (
        name,
        "fraction",
    )
    rounded = (Decimal(numerator) / Decimal(denominator)).quantize(
        Decimal("0.000000000000001"), rounding=ROUND_HALF_EVEN
    )
    assert Decimal(row["ratio_decimal"]) == rounded, (name, "decimal")
    checked.append(name)


for name, field in field_map.items():
    verify_ratio(name, int(repair[field]), int(reacquisition[field]))

verify_ratio(
    "wall_ns",
    int(Decimal(repair["elapsed_ms"]) * 1_000_000),
    int(Decimal(reacquisition["elapsed_ms"]) * 1_000_000),
)

assert len(checked) == 8
print(
    json.dumps(
        {
            "decision": "PASS_RETAINED_RESULT_PROVENANCE_SCOPED",
            "fresh_allocation": False,
            "formal_invocation": result["formal_invocation"],
            "formal_reruns": result["formal_reruns"],
            "comparator_match": True,
            "source_blob_claim_matches_result": True,
            "recomputed_ratio_fields": checked,
            "ratio_count": len(checked),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
)
