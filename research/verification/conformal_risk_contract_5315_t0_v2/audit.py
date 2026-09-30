"""Raw-only independent audit; does not import candidate.py or run.py."""

import hashlib
import json
import sys
from pathlib import Path


def main():
    root = Path(__file__).parent
    raw = json.loads(Path(sys.argv[1]).read_text())
    calibration = json.loads((root / "calibration.json").read_text())
    records = json.loads((root / "calibration_records.json").read_bytes())
    digest = "sha256:" + hashlib.sha256((root / "calibration_records.json").read_bytes()).hexdigest()
    assert raw["status"] == "T0_SUCCESSOR_EXECUTED"
    assert raw["authority_granted"] is False
    assert digest == calibration["calibration_digest"] == raw["calibration"]["digest"]
    assert len(records) == calibration["n"] == 199
    assert sum(records) == calibration["errors"] == 8
    upper = calibration["n"] / (calibration["n"] + 1) * (calibration["errors"] / calibration["n"]) + calibration["loss_bound"] / (calibration["n"] + 1)
    assert upper == raw["calibration"]["crc_upper"] == 0.045
    assert upper <= raw["alpha"]
    arms = {arm["id"]: arm for arm in raw["arms"]}
    iid = arms["iid_reference"]
    assert iid["certificate_decision"] == "ALLOW_MARGINAL_CLAIM_ONLY"
    assert iid["empirical_population_loss"] == 0.04
    assert iid["conditional_selected_risk"] == 1.0
    assert iid["fail_closed_singleton"] == "UNCERTAIN"
    expected = {
        "temporal_shift": "REJECT_STALE",
        "ui_layout_shift": "REJECT_POPULATION_MISMATCH",
        "task_family_shift": "REJECT_POPULATION_MISMATCH",
        "adaptive_repeated_query": "REJECT_ASSUMPTION_INVALID",
    }
    for name, reason in expected.items():
        assert arms[name]["certificate_decision"] == reason
        assert arms[name]["fail_closed_singleton"] == "UNCERTAIN"
    decisions = {control["id"]: control["decision"] for control in raw["controls"]}
    assert decisions == {
        "tampered_nonempty_digest": "REJECT_CALIBRATION_DIGEST_MISMATCH",
        "changed_record_bytes": "REJECT_CALIBRATION_DIGEST_MISMATCH",
        "summary_count_mismatch": "REJECT_CALIBRATION_STATS_MISMATCH",
        "conditional_scope": "REJECT_UNSUPPORTED_SCOPE",
        "population_mismatch": "REJECT_POPULATION_MISMATCH",
        "stale_calibration": "REJECT_STALE",
    }
    print("AUDIT_PASS: retained bytes/digest, 199 rows/8 errors, CRC arithmetic, selective-risk boundary, 4 shift arms, 6/6 corruption controls, zero authority")


if __name__ == "__main__":
    main()
