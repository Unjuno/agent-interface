"""One-shot formal runner; refuses an existing output directory."""
import json
import sys
from pathlib import Path

from .design import EXHAUSTIVE, OFAT, PAIRWISE, THREE_WAY, result


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m research.analysis.constrained_interaction_testing_5330_t0_v1.run OUTPUT_DIR")
    out = Path(sys.argv[1])
    if out.exists():
        raise SystemExit(f"STOP_OUTPUT_EXISTS: {out}")
    out.mkdir(parents=True)
    raw = {
        "schema": "constrained-interaction-5330-t0-raw-v1",
        "factors": list(__import__("research.analysis.constrained_interaction_testing_5330_t0_v1.design", fromlist=["FACTORS"]).FACTORS),
        "designs": {
            "OFAT": result(OFAT), "PAIRWISE": result(PAIRWISE),
            "THREE_WAY": result(THREE_WAY), "EXHAUSTIVE": result(EXHAUSTIVE),
        },
    }
    (out / "raw.json").write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    summary = {
        "pair_detection_contrast": not raw["designs"]["OFAT"]["pair_hazard_detected"] and raw["designs"]["PAIRWISE"]["pair_hazard_detected"],
        "triple_detection": raw["designs"]["THREE_WAY"]["triple_hazard_detected"],
        "pair_coverage_complete": raw["designs"]["PAIRWISE"]["pair_coverage"] == 24,
        "triple_coverage_complete": raw["designs"]["THREE_WAY"]["triple_coverage"] == 32,
        "strictly_smaller_than_exhaustive": all(raw["designs"][name]["case_count"] < 16 for name in ("PAIRWISE", "THREE_WAY")),
    }
    passed = all(summary.values())
    summary["status"] = "PASS_DESIGN_SENSITIVITY_ONLY" if passed else "FAIL_DESIGN_SENSITIVITY"
    (out / "summary.json").write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
