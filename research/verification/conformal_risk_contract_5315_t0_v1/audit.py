"""Independent raw-result audit; imports neither candidate nor run."""

import json
import sys
from pathlib import Path


def main():
    raw = json.loads(Path(sys.argv[1]).read_text())
    assert raw["status"] == "T0_EXECUTED"
    assert raw["authority_granted"] is False
    crc = raw["crc"]
    expected = crc["n"] / (crc["n"] + 1) * (crc["errors"] / crc["n"]) + crc["loss_bound"] / (crc["n"] + 1)
    assert abs(raw["crc"]["finite_sample_upper"] - expected) < 1e-15
    assert expected <= raw["alpha"]
    by_id = {arm["id"]: arm for arm in raw["arms"]}
    iid = by_id["iid_reference"]["crc_marginal"]
    assert iid["empirical_population_loss"] <= raw["alpha"]
    assert iid["conditional_selected_risk"] > raw["alpha"]
    assert iid["conditional_selected_risk"] == 1.0
    assert iid["certificate_decision"] == "ALLOW_MARGINAL_CLAIM_ONLY"
    assert iid["claim_supported"] is True
    expected_rejections = {
        "temporal_shift": "REJECT_STALE",
        "ui_layout_shift": "REJECT_VERSION_MISMATCH",
        "task_family_shift": "REJECT_POPULATION_MISMATCH",
        "adaptive_repeated_query": "REJECT_ASSUMPTION_INVALID",
    }
    for name, reason in expected_rejections.items():
        arm = by_id[name]
        assert arm["crc_marginal"]["certificate_decision"] == reason
        assert arm["fail_closed_singleton"]["output"] == "UNCERTAIN"
        assert arm["set_valued"]["output"] == "{PASS,FAIL}"
    assert len(raw["controls"]) == 5
    assert all(control["decision"].startswith("REJECT_") for control in raw["controls"])
    print("AUDIT_PASS: finite-sample arithmetic, marginal/conditional counterexample, shift rejection, 5/5 corruption controls, zero authority")


if __name__ == "__main__":
    main()
