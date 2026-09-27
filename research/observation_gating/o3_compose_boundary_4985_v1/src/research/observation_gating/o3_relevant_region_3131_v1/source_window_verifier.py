import json
import sys

from research.observation_gating.o3_relevant_region_successor_v1.gate import evaluate_region


def verify_source_window(evidence, trusted_window):
    """Reject transport evidence unless it is bound to the observed X11 window."""
    if str(evidence.get("source_window")) != str(trusted_window):
        return False, "source_window_mismatch"
    return True, "source_window_bound"


def main(path):
    payload = json.load(open(path))
    trusted = payload["fixture_window"]
    rows = []
    for row in payload["rows"]:
        evidence = {
            "observation_id": "live-1",
            "intent_epoch": 1,
            "region_id": "entry",
            "coverage": "COMPLETE",
            "freshness": "CURRENT",
            "effect_binding": "BOUND",
            "authority_grants": 0,
            "ambiguous": False,
            "source_window": row["window"] if row["case"] != "forged_complete" else "9999999",
        }
        if row["case"] == "stale_frame": evidence["freshness"] = "STALE"
        if row["case"] == "partial_coverage": evidence["coverage"] = "PARTIAL"
        if row["case"] == "wrong_region": evidence["region_id"] = "toolbar"
        if row["case"] == "ambiguous": evidence["ambiguous"] = True
        bound, reason = verify_source_window(evidence, trusted)
        decision = evaluate_region(evidence, observation_id="live-1", intent_epoch=1, region_id="entry")
        admitted = bound and decision.admitted
        rows.append({"case": row["case"], "admitted": admitted,
                     "binding_reason": reason, "gate_reason": decision.reason})
    expected = {"complete_current": True, "stale_frame": False,
                "partial_coverage": False, "wrong_region": False,
                "ambiguous": False, "forged_complete": False}
    result = {"decision": "PASS_O3_SOURCE_WINDOW_BOUND_SCOPED"
              if all(r["admitted"] == expected[r["case"]] for r in rows)
              else "FAIL_SOURCE_WINDOW_BINDING", "trusted_window": trusted, "rows": rows}
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main(sys.argv[1:])
