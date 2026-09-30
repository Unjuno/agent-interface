import importlib.util
import itertools
import json
from fractions import Fraction
from pathlib import Path

root = Path(__file__).parent
data_bytes = (root / "cases.json").read_bytes()
data = json.loads(data_bytes)
spec = importlib.util.spec_from_file_location("candidate", root / "candidate.py")
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)
result = candidate.compute(data, data_bytes, (root / "candidate.py").read_bytes(),
                           "HOST_PYTHON_ONLY_NOT_CONTAINER", "windows/amd64")
candidate_rows = {row["case_id"]: row for row in result["rows"]}
expected = {}
vertices = 0
for claim in data["claims"]:
    nominal = sum((Fraction(item["margin"]) for item in claim["evidence"]), Fraction())
    causes = claim["latent_causes"]
    ids = [item["cause_id"] for item in causes]
    bounds = {item["cause_id"]: Fraction(item["bound"]) for item in causes}
    worst = None
    for bits in itertools.product((False, True), repeat=len(ids)):
        vertices += 1
        latent = {cause_id: bounds[cause_id] if active else Fraction()
                  for cause_id, active in zip(ids, bits)}
        loss = sum((Fraction(edge["adverse_weight"]) * latent[edge["cause_id"]]
                    for edge in claim["influence_edges"]), Fraction())
        score = nominal - loss
        worst = score if worst is None else min(worst, score)
    grouped = {cause_id: Fraction() for cause_id in ids}
    for edge in claim["influence_edges"]:
        grouped[edge["cause_id"]] += Fraction(edge["adverse_weight"])
    status = "ROBUST" if worst > 0 else ("SENSITIVE" if nominal > 0 else "ABSTAIN")
    expected[claim["case_id"]] = {
        "case_id": claim["case_id"],
        "matched_pair": claim["matched_pair"],
        "nominal_margin": f"{nominal.numerator}/{nominal.denominator}",
        "worst_case_margin": f"{worst.numerator}/{worst.denominator}",
        "cause_risks": {key: f"{(grouped[key] * bounds[key]).numerator}/{(grouped[key] * bounds[key]).denominator}"
                        for key in sorted(grouped)},
        "status": status,
    }
assert candidate_rows == expected, "candidate differs from independent vertex oracle"
sensitive = {key for key, row in expected.items() if row["status"] == "SENSITIVE"}
budget = len(expected) // 4
margin_abstain = {row["case_id"] for row in sorted(expected.values(),
                  key=lambda row: (Fraction(row["nominal_margin"]), row["case_id"]))[:budget]}
margin_unsafe = sum(key not in margin_abstain and Fraction(row["worst_case_margin"]) <= 0
                    for key, row in expected.items())
assert len(sensitive) == 4
assert margin_unsafe >= 1
assert all(Fraction(expected[key]["worst_case_margin"]) > 0
           for key in set(expected) - sensitive)
assert vertices == 128
print("PASS_HOST_PYTHON_CONSTRUCTION_ONLY claims=16 vertices=128 sensitivity_abstentions=4/16 margin_only_residual_unsafe=2 container=False formal_result=False")

