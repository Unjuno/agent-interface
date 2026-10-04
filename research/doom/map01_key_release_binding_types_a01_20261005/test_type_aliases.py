"""Regressions for JSON booleans aliasing integer step and sequence fields."""
import copy
import importlib.util
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
V1_CANDIDATE = HERE.parent / "map01_key_release_binding_a01_20261005" / "candidate.py"
SPEC = importlib.util.spec_from_file_location("binding_candidate_v1", V1_CANDIDATE)
V1 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(V1)
V2_CANDIDATE = HERE / "candidate.py"
SPEC2 = importlib.util.spec_from_file_location("binding_candidate_v2", V2_CANDIDATE)
V2 = importlib.util.module_from_spec(SPEC2)
SPEC2.loader.exec_module(V2)
FIXTURE = json.loads((HERE.parent / "map01_key_release_binding_a01_20261005" / "fixture.json").read_text())


def test_boolean_step_does_not_alias_integer_step_one():
    case = copy.deepcopy(FIXTURE)
    case["execution"]["step"] = 1
    case["admissions"][0]["step"] = 1
    case["key_ups"][0]["step"] = True

    assert V1.reduce(case) == ("PASS", "complete")
    assert V2.reduce(case) == ("FAIL", "invalid_up_context_type")


def test_boolean_sequence_does_not_satisfy_positive_integer_sequence():
    case = copy.deepcopy(FIXTURE)
    case["admissions"][0]["seq"] = 0
    case["key_ups"][0]["seq"] = True
    case["releases"][0]["seq"] = 2

    assert V1.reduce(case) == ("PASS", "complete")
    assert V2.reduce(case) == ("FAIL", "invalid_sequence_type")


def test_boolean_admission_sequence_is_rejected():
    case = copy.deepcopy(FIXTURE)
    case["admissions"][0]["seq"] = True

    assert V1.reduce(case) == ("PASS", "complete")
    assert V2.reduce(case) == ("FAIL", "invalid_sequence_type")


def test_float_release_sequence_is_rejected():
    case = copy.deepcopy(FIXTURE)
    case["releases"][0]["seq"] = 3.0

    assert V1.reduce(case) == ("PASS", "complete")
    assert V2.reduce(case) == ("FAIL", "invalid_sequence_type")


def test_admission_must_match_execution_step_context():
    case = copy.deepcopy(FIXTURE)
    case["execution"]["step"] = 3

    assert V1.reduce(case) == ("PASS", "complete")
    assert V2.reduce(case) == ("FAIL", "unbound_or_cross_execution_admission")
