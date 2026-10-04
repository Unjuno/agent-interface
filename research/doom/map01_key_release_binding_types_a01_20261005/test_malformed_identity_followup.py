"""Post-run regressions for unhashable JSON key-up identity fields."""
import copy
import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
FIXTURE = json.loads((HERE / "fixture.json").read_text())

def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

FROZEN_CANDIDATE = load("frozen_candidate_for_repro", "candidate.py")
FROZEN_AUDIT = load("frozen_audit_for_repro", "audit.py")
HARDENED_CANDIDATE = load("hardened_candidate_for_followup", "candidate_hardened.py")
HARDENED_AUDIT = load("hardened_audit_for_followup", "audit_hardened.py")

def test_frozen_paths_reproduce_unhashable_admission_id_exception():
    case = copy.deepcopy(FIXTURE)
    case["key_ups"][0]["admission_id"] = []
    with pytest.raises(TypeError):
        FROZEN_CANDIDATE.reduce(case)
    with pytest.raises(TypeError):
        FROZEN_AUDIT.oracle(case)

def test_hardened_paths_reject_unhashable_key_up_identity_fields():
    for field in ("admission_id", "execution_id", "key"):
        for invalid in ([], {}):
            case = copy.deepcopy(FIXTURE)
            case["key_ups"][0][field] = invalid
            expected = ("FAIL", "invalid_up_context_type")
            assert HARDENED_CANDIDATE.reduce(case) == expected
            assert HARDENED_AUDIT.oracle(case) == expected
