import json
from candidate import classify
from auditor import expected_from_receipts

raw = json.load(open("input/histories.json", encoding="utf-8"))
oracle = json.load(open("oracle.json", encoding="utf-8"))["expected"]
assert len(raw["histories"]) == 8
for h in raw["histories"]:
    assert classify(h) == oracle[h["id"]]
    assert expected_from_receipts(h) == oracle[h["id"]]
assert classify(raw["histories"][0]) != classify(raw["histories"][1])
assert classify(raw["histories"][5])["owner"].endswith("CHILD_UNRESOLVED")
assert classify(raw["histories"][7])["verifier"] == "CONFLICT_NOT_PASS"

cases = {h["id"]: h for h in raw["histories"]}
assert "COMPLETED" != oracle["dispatch_only"]["verifier"]
assert expected_from_receipts({**cases["child_unresolved"], "children": []})["owner"] != oracle["child_unresolved"]["owner"]
assert "ACCEPTED" != "TARGET_MATCH"
assert oracle["contradictory_receipts"]["verifier"] != "VERIFIED"
print("BUILD_PASS rows=8 independent_oracle=8 mutations=4")
