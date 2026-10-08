"""Execute the fixed deterministic Issue #5315 T0 scenarios."""

import argparse
import json
from pathlib import Path

from candidate import check_certificate, crc_upper


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    root = Path(__file__).parent
    fixture = json.loads((root / "scenarios.json").read_text())
    cal = fixture["calibration"]
    upper = crc_upper(cal["n"], cal["errors"], cal["loss_bound"])
    arms = []
    for arm in fixture["arms"]:
        cert = check_certificate(cal, arm)
        marginal = arm["selected_errors"] / arm["n"]
        selective = arm["selected_errors"] / arm["selected"]
        arms.append(
            {
                "id": arm["id"],
                "raw_score": {"false_passes": arm["selected_errors"], "coverage": arm["selected"]},
                "fixed_checklist": {"false_passes": arm["checklist_errors"]},
                "crc_marginal": {
                    "certificate_decision": cert,
                    "empirical_population_loss": marginal,
                    "conditional_selected_risk": selective,
                    "claim_supported": cert == "ALLOW_MARGINAL_CLAIM_ONLY" and upper <= fixture["alpha"],
                },
                "fail_closed_singleton": {
                    "output": "UNCERTAIN",
                    "conditional_selective_certificate": False,
                },
                "set_valued": {"output": "{PASS,FAIL}"},
            }
        )
    controls = []
    for corruption in fixture["corruptions"]:
        bad_cal = dict(cal)
        bad_arm = dict(fixture["arms"][0])
        if corruption == "missing_calibration_digest":
            bad_cal["calibration_digest"] = ""
        elif corruption == "population_mismatch":
            bad_arm["population_id"] = "other-population"
        elif corruption == "version_mismatch":
            bad_arm["version"] = "other-version"
        elif corruption == "stale_calibration":
            bad_arm["age_hours"] = bad_cal["freshness_limit_hours"] + 1
        elif corruption == "exchangeability_broken":
            bad_arm["exchangeable"] = False
        controls.append({"corruption": corruption, "decision": check_certificate(bad_cal, bad_arm)})
    result = {
        "status": "T0_EXECUTED",
        "alpha": fixture["alpha"],
        "crc": {
            "n": cal["n"],
            "errors": cal["errors"],
            "loss_bound": cal["loss_bound"],
            "empirical_risk": cal["errors"] / cal["n"],
            "finite_sample_upper": upper,
        },
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
