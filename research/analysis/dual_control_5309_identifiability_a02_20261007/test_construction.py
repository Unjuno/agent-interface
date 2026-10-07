#!/usr/bin/env python3
"""Behavioral construction controls; not the formal A02 allocation."""
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from auditor import audit, pairwise_separator


ROOT = Path(__file__).resolve().parent
fixture = json.loads((ROOT / "fixture.json").read_text())
truth = json.loads((ROOT / "oracle_truth.json").read_text())


def seal(raw):
    raw.pop("raw_sha256", None)
    payload = json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()
    raw["raw_sha256"] = hashlib.sha256(payload).hexdigest()
    return raw


def mutated(raw, edit):
    value = copy.deepcopy(raw)
    edit(value)
    seal(value)
    return audit(value, fixture, truth)


def main():
    proc = subprocess.run([sys.executable, str(ROOT / "candidate.py")], check=True, capture_output=True, text=True)
    raw = json.loads(proc.stdout)
    assert audit(raw, fixture, truth)["status"] == "PASS_METHOD_SCOPED"
    assert raw["generic_one_step"]["information_gain_bits"] == 1.0

    # Pairwise negative/positive controls and expiry-boundary checks.
    separator = truth["scenarios"]["separator_available"]
    pair = pairwise_separator(separator, "s_b", "s_h")
    assert pair["separated"] is True and pair["sequence"] == ["witness"]
    equal_history = copy.deepcopy(separator)
    equal_history["observations"]["witness"]["s_h"] = "benign_witness"
    assert pairwise_separator(equal_history, "s_b", "s_h")["separated"] is False
    assert pairwise_separator(truth["scenarios"]["no_separator"], "n_b", "n_h")["separated"] is False
    assert pairwise_separator(truth["scenarios"]["expiry_before_separator"], "e_b", "e_h")["separated"] is False
    assert pairwise_separator(truth["scenarios"]["one_step_null"], "z_b", "z_h")["sequence"] == ["witness"]

    # Raw-only mutations: refusal leakage, authority escalation, false repeat,
    # and a missing exogenous opportunity must all fail closed.
    controls = [
        lambda r: r["refused_action_event"].update(observation="would_have_seen_hazard"),
        lambda r: r.update(authority_granted=True),
        lambda r: r["repeated_benign_branch"]["events"][0].update(observation="hazard_witness"),
        lambda r: r.update(exogenous_opportunity_stream=["different-stream"]),
    ]
    for edit in controls:
        assert mutated(raw, edit)["status"] == "FAIL_A02_AUDIT_CONTRACT"

    print("construction behavioral controls: 9 PASS; 4 corrupted raws rejected")


if __name__ == "__main__":
    main()
