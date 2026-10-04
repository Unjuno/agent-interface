"""Independent checks over the saved A03 comparison result."""
import json
from pathlib import Path


data = json.loads(Path("RESULT.json").read_text(encoding="utf-8"))
assert data["schema"] == "scorer-feedback-attribution-a03-result-v1"
for name in ("admission_tied_to_lower", "release_tied_to_upper"):
    old = data["cases"][name]["a01"][0]
    new = data["cases"][name]["a03"][0]
    assert old["status"] == "TEMPORALLY_UNIQUE" and old["intent_token"] == "intent-a"
    assert new["status"] == "UNRESOLVED" and new["intent_token"] is None
    assert new["reason"] == "endpoint_tie_without_authenticated_order"
    assert new["causal_attribution"] == "NOT_ESTABLISHED"
strict = data["cases"]["strictly_bracketed"]["a03"][0]
assert strict["status"] == "TEMPORALLY_UNIQUE" and strict["intent_token"] == "intent-a"
assert all(row["causal_attribution"] == "NOT_ESTABLISHED"
           for case in data["cases"].values() for variant in case.values() for row in variant)
print("A03 saved-result audit: PASS (3 comparisons; endpoint ties fail closed; causal labels absent)")
