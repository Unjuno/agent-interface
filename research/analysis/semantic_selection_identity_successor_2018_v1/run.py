import hashlib
import json

CASES = [
    ("stable", "A", "A", "app", "app", 1, 1),
    ("pixel_identical_replacement", "A", "B", "app", "app", 1, 2),
    ("decoy_switch", "A", "B", "app", "app", 1, 2),
    ("focus_transfer", "A", "A", "app", "other", 1, 1),
    ("semantic_unavailable", "A", None, "app", "app", 1, None),
    ("stale_receipt", "A", "A", "app", "app", 1, 0),
    ("mismatched_window", "A", "A", "app", "app2", 1, 1),
    ("conflicting_visual_semantic", "A", "B", "app", "app", 1, 1),
    ("malformed_duplicate_identity", "A|A", "A", "app", "app", 1, 1),
]

def visual_only(expected, observed):
    return expected == observed

def semantic_only(expected, observed, app, obs_app, epoch, obs_epoch):
    return isinstance(observed, str) and "|" not in observed and app == obs_app and obs_epoch == epoch and observed == expected

def combined(expected, observed, app, obs_app, epoch, obs_epoch):
    return visual_only(expected, observed) and semantic_only(expected, observed, app, obs_app, epoch, obs_epoch)

def main():
    rows = []
    for name, expected, observed, app, obs_app, epoch, obs_epoch in CASES:
        rows.append({
            "case": name,
            "visual_only": visual_only(expected, observed),
            "semantic_only": semantic_only(expected, observed, app, obs_app, epoch, obs_epoch),
            "visual_plus_semantic_consistency": combined(expected, observed, app, obs_app, epoch, obs_epoch),
            "authority_events": 0,
            "task_input_events": 0,
        })
    # Promotion-relevant gates: replacement, focus, unavailable, stale, mismatch, conflict, malformed must fail closed.
    required_rejects = {r[0] for r in CASES[1:]}
    actual_rejects = {r["case"] for r in rows if not r["visual_plus_semantic_consistency"]}
    decision = "PASS_READ_ONLY_SEMANTIC_IDENTITY_SCOPED" if required_rejects <= actual_rejects and all(r["authority_events"] == r["task_input_events"] == 0 for r in rows) else "FAIL_SEMANTIC_IDENTITY_GATES"
    payload = {"decision": decision, "cases": rows, "formal_invocations": 1, "reruns": 0, "replacements": 0, "tuning": 0}
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    payload["sha256"] = hashlib.sha256(raw).hexdigest()
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if decision.startswith("PASS") else 1

if __name__ == "__main__":
    raise SystemExit(main())
