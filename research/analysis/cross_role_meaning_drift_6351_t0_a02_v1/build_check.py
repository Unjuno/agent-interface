import json
from candidate import run
from auditor import expected

raw=json.load(open("input/histories.json",encoding="utf-8"))
oracle=json.load(open("oracle.json",encoding="utf-8"))["expected"]
rows=run("input/histories.json")
assert len(rows)==8
for h,r in zip(raw["histories"],rows):
    assert expected(h)==oracle[h["id"]]
    assert r["typed"]==expected(h)
assert expected({**raw["histories"][2],"verify_epoch":5})=="CONFLICT_NOT_PASS"
assert expected({**raw["histories"][5],"children":[]})!="VERIFIED_WITH_CHILD_OBLIGATION"
assert expected({**raw["histories"][7],"receipt_conflict":False,"verify_epoch":5})=="CONFLICT_NOT_PASS"
assert raw["histories"][0]["dispatch"]=="ACCEPTED" and raw["histories"][0]["effect"]=="NONE"
print("BUILD_PASS histories=8 mutations_applied=4")
