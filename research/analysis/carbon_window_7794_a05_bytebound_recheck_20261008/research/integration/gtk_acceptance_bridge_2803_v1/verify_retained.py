"""Independent, no-rerun verifier for retained #2801 GTK rows."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RETAINED = ROOT.parent / "gtk_acceptance_bridge_2803_v1" / "retained"
NAMES = ["useful", "unavailable", "guarded", "no_effect", "partial", "stale_repair", "ambiguous", "cleanup_failure"]
EXPECTED = ["SUCCESS", "YIELD", "YIELD", "NONE", "PARTIAL", "YIELD", "YIELD", "YIELD"]

def load(name):
    return json.loads((RETAINED / name / "row.json").read_text(encoding="utf-8"))

def main():
    rows = [load(name) for name in NAMES]
    actual = [r.get("disposition") for r in rows]
    checks = {
        "case_order": [r.get("case") for r in rows] == NAMES,
        "expected_dispositions": actual == EXPECTED,
        "authority_zero": all(r.get("formal_receipt", {}).get("authority_grants") == 0 for r in rows),
        "useful_effect": rows[0].get("independent_effect", {}).get("saved") is True,
        "partial_effect": rows[4].get("independent_effect", {}).get("saved") is True,
        "stale_no_replay": rows[5].get("replay_allowed") is False and rows[5].get("adapter_result", {}).get("raw_dispatch", {}).get("result", {}).get("backend_emissions") == 0,
        "ambiguous_no_replay": rows[6].get("replay_allowed") is False and rows[6].get("independent_effect") is None,
        "cleanup_failure_not_success": rows[7].get("cleanup") == "failed" and rows[7].get("disposition") != "SUCCESS",
        "release_or_safe_refusal": all(r.get("formal_receipt", {}).get("cleanup", {}).get("status") in {"clean", "repaired", "failed"} for r in rows),
    }
    result = {"decision": "PASS_ACCEPTANCE_BRIDGE_SCOPED" if all(checks.values()) else "FAIL_ACCEPTANCE_BRIDGE", "checks": checks, "actual": actual, "expected": EXPECTED, "rerun": False, "scope": "retained GTK matrix evidence only"}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["decision"].startswith("PASS") else 1

if __name__ == "__main__":
    raise SystemExit(main())
