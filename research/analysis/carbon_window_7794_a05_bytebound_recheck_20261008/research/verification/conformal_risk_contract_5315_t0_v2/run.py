"""Execute the fixed, deterministic Issue #5315 successor scenarios once."""

import argparse
import json
from pathlib import Path

from candidate import check_certificate, crc_upper


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    root = Path(__file__).parent
    cal = json.loads((root / "calibration.json").read_text())
    scenarios = json.loads((root / "scenarios.json").read_text())
    record_bytes = (root / "calibration_records.json").read_bytes()
    records = json.loads(record_bytes)
    upper = crc_upper(cal["n"], cal["errors"], cal["loss_bound"])
    arms = []
    for arm in scenarios["arms"]:
        decision = check_certificate(cal, arm, record_bytes, records)
        arms.append({
            "id": arm["id"],
            "certificate_decision": decision,
            "empirical_population_loss": arm["selected_errors"] / arm["n"],
            "conditional_selected_risk": arm["selected_errors"] / arm["selected"],
            "fail_closed_singleton": "UNCERTAIN",
            "set_valued": "{PASS,FAIL}",
        })
    controls = []
    bad = dict(cal)
    bad["calibration_digest"] = "sha256:tampered-nonempty"
    controls.append({"id": "tampered_nonempty_digest", "decision": check_certificate(bad, scenarios["arms"][0], record_bytes, records)})
    mutated_bytes = record_bytes.replace(b"1,1,1", b"0,1,1", 1)
    mutated_rows = json.loads(mutated_bytes)
    controls.append({"id": "changed_record_bytes", "decision": check_certificate(cal, scenarios["arms"][0], mutated_bytes, mutated_rows)})
    bad = dict(cal)
    bad["errors"] -= 1
    controls.append({"id": "summary_count_mismatch", "decision": check_certificate(bad, scenarios["arms"][0], record_bytes, records)})
    bad = dict(cal)
    bad["claim_scope"] = "CONDITIONAL_SELECTED_RISK"
    controls.append({"id": "conditional_scope", "decision": check_certificate(bad, scenarios["arms"][0], record_bytes, records)})
    bad_arm = dict(scenarios["arms"][0])
    bad_arm["population_id"] = "other-population"
    controls.append({"id": "population_mismatch", "decision": check_certificate(cal, bad_arm, record_bytes, records)})
    bad_arm = dict(scenarios["arms"][0])
    bad_arm["age_hours"] = cal["freshness_limit_hours"] + 1
    controls.append({"id": "stale_calibration", "decision": check_certificate(cal, bad_arm, record_bytes, records)})
    result = {
        "status": "T0_SUCCESSOR_EXECUTED",
        "alpha": cal["target_risk"],
        "calibration": {"n": cal["n"], "errors": cal["errors"], "digest": cal["calibration_digest"], "crc_upper": upper},
        "arms": arms,
        "controls": controls,
        "authority_granted": False,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "crc_upper": upper, "arms": len(arms), "controls": len(controls)}))


if __name__ == "__main__":
    main()
