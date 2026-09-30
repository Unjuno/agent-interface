import copy
import json
from pathlib import Path

from audit import EXPECTED, invalid_reasons


def test_formal_raw_matches_independent_expectations():
    raw = json.loads(Path("out/raw.json").read_text())
    assert invalid_reasons(raw) == []
    assert len(raw["cases"]) == len(EXPECTED) == 5


def test_hidden_read_is_not_claimed_as_detected():
    raw = json.loads(Path("out/raw.json").read_text())
    row = next(r for r in raw["cases"] if r["case"] == "hidden_read")
    assert row["policies"]["SEMANTIC_GATE"]["decision"] == "PARALLEL"
    assert row["policies"]["SEMANTIC_GATE"]["serial_outcome_divergence"] is True
    outcomes = row["oracle"]["legal_serial_outcomes"]
    concurrent = row["oracle"]["observed_concurrent_outcome"]
    assert concurrent in outcomes
    assert outcomes[0] != outcomes[1]
    # Raw's boolean compares against the fixed b-then-a schedule only. The
    # independently audited schedule set exposes the hidden-read divergence.
    assert row["oracle"]["concurrent_matches_serial"] is True


def test_mutation_controls_reject_corruption():
    raw = json.loads(Path("out/raw.json").read_text())
    changed = copy.deepcopy(raw)
    changed["authority_grants"] = 1
    assert invalid_reasons(changed)
    changed = copy.deepcopy(raw)
    changed["cases"].pop()
    assert invalid_reasons(changed)
