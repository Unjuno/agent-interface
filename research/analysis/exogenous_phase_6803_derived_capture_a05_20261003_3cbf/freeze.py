"""Produce the hash-bound preregistration artifact; refuses existing freeze."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OLD = ROOT.parent / "exogenous_opportunity_5694_matched_phase_a04_20261002"
FILES = ("candidate.py", "audit.py", "legacy_probe.py", "prepare.py", "fixture.json",
         "runner.py", "freeze.py", "test_contract.py", "PREREGISTRATION.md")

if __name__ == "__main__":
    value = {"schema": "derived-capture-freeze-v1", "issue": 6969,
             "predecessor": 6803, "intake_main": "6d7ce9693caae8c123fda532da64888f6006dcb9",
             "allocation": "PHASE-6803-A05-ORBSTACK-20261003-3CBF-01",
             "source_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in FILES},
             "legacy_sha256": {p: hashlib.sha256((OLD / p).read_bytes()).hexdigest() for p in ("candidate.py", "fixture.json")}}
    with (ROOT / "FREEZE.json").open("x") as target:
        json.dump(value, target, sort_keys=True, indent=2)
        target.write("\n")
    print("SOURCE_FREEZE_WRITTEN files=" + str(len(FILES)))
