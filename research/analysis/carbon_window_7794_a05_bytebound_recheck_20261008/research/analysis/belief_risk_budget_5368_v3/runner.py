"""One-shot finite exact-rational risk/availability replay."""
import json
import platform
import sys
from pathlib import Path

from model import CASES, evaluate, fraction_text

SOURCE_MAIN = "4439161abd6f8ccf276babc1c39c43428394e773"
POLICIES = ("MAP", "WORST_CASE", "RISK_BUDGET", "EXPECTED_UTILITY")


def build_raw() -> dict:
    rows = []
    for case_id, (reported, actual) in CASES.items():
        for policy in POLICIES:
            rows.append({
                "case_id": case_id,
                "reported": fraction_text(reported),
                "actual": fraction_text(actual),
                "branches": {"safe": fraction_text(1-actual), "unsafe": fraction_text(actual)},
                **evaluate(policy, reported, actual),
                "authority": False,
                "effect": False,
            })
    return {
        "allocation": "belief-risk-budget-5368-t0-20260930-01",
        "source_main": SOURCE_MAIN,
        "runtime": {"python": platform.python_version(), "platform": platform.platform()},
        "cases": len(CASES), "policies": list(POLICIES), "rows": rows,
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python3 -B runner.py RAW.json")
    path = Path(sys.argv[1])
    if path.exists():
        raise SystemExit("STOP_OUTPUT_ALREADY_EXISTS")
    raw = build_raw()
    path.write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "RAW_WRITTEN", "rows": len(raw["rows"]), "raw": str(path)}))
