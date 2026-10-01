import json
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).parent


def test_candidate_reproduces_frozen_raw():
    before = (HERE / "raw.json").read_bytes()
    subprocess.run([sys.executable, "-I", str(HERE / "candidate.py")], check=True, capture_output=True)
    assert (HERE / "raw.json").read_bytes() == before


def test_independent_audit_accepts_raw():
    proc = subprocess.run([sys.executable, "-I", str(HERE / "audit.py")], check=True, capture_output=True, text=True)
    assert json.loads(proc.stdout)["audit"] == "PASS"


def test_contract_policy_scope_and_false_admissions():
    audit = json.loads((HERE / "audit.json").read_text())
    assert audit["contract_matches_expected"] == 11
    assert audit["unsafe_any_singleton_cases"] == 3
    assert audit["trusted_singleton_recovered"] is True
