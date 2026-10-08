"""Independent finite-matrix oracle; intentionally does not import the monitor."""

import json
import sys


# Expected acceptance sequences and final states are fixed from the protocol
# contract, not reconstructed from protocol_lifecycle_5320.EDGES.
EXPECTED = {
    "release_before_acquire": {
        "CONVENTION_ONLY": ([True], "OFFERED"),
        "RUNTIME_AUTOMATON": ([False], "OFFERED"),
        "LINEAR_PROTOCOL": ([False], "OFFERED"),
        "MULTIPARTY_PROTOCOL": ([False], "OFFERED"),
    },
    "expire_before_commit": {
        "CONVENTION_ONLY": ([True, True, True, True], "EXPIRED"),
        "RUNTIME_AUTOMATON": ([True, True, True, False], "EXPIRED"),
        "LINEAR_PROTOCOL": ([True, True, True, False], "EXPIRED"),
        "MULTIPARTY_PROTOCOL": ([True, True, True, False], "EXPIRED"),
    },
    "unknown_recovery": {
        p: ([True] * 6, "RELEASED")
        for p in ("CONVENTION_ONLY", "RUNTIME_AUTOMATON", "LINEAR_PROTOCOL", "MULTIPARTY_PROTOCOL")
    },
    "capability_replay": {
        "CONVENTION_ONLY": ([True, True], "PREPARED"),
        "RUNTIME_AUTOMATON": ([True, True], "PREPARED"),
        "LINEAR_PROTOCOL": ([True, False], "LEASED"),
        "MULTIPARTY_PROTOCOL": ([True, True], "PREPARED"),
    },
    "role_mismatch": {
        "CONVENTION_ONLY": ([True, True], "PREPARED"),
        "RUNTIME_AUTOMATON": ([True, True], "PREPARED"),
        "LINEAR_PROTOCOL": ([True, True], "PREPARED"),
        "MULTIPARTY_PROTOCOL": ([True, False], "LEASED"),
    },
    "unknown_event": {
        p: ([False], "OFFERED")
        for p in ("CONVENTION_ONLY", "RUNTIME_AUTOMATON", "LINEAR_PROTOCOL", "MULTIPARTY_PROTOCOL")
    },
}


def audit(path):
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    errors = []
    if set(raw) != set(EXPECTED):
        errors.append("scenario set mismatch")
    for scenario, policies in EXPECTED.items():
        for policy, (accepted, final_state) in policies.items():
            got = raw.get(scenario, {}).get(policy)
            if got is None:
                errors.append(f"missing {scenario}/{policy}")
                continue
            if got.get("accepted") != accepted:
                errors.append(f"acceptance mismatch {scenario}/{policy}")
            if got.get("final_state") != final_state:
                errors.append(f"state mismatch {scenario}/{policy}")
            if got.get("authority_created") is not False:
                errors.append(f"authority leakage {scenario}/{policy}")
            if got.get("effect_claim_created") is not False:
                errors.append(f"effect claim leakage {scenario}/{policy}")
    return errors


if __name__ == "__main__":
    errors = audit(sys.argv[1])
    print(json.dumps({"status": "PASS_READONLY" if not errors else "FAIL_AUDIT",
                      "scenarios": len(EXPECTED), "policy_cases": sum(map(len, EXPECTED.values())),
                      "errors": errors}, sort_keys=True))
    raise SystemExit(bool(errors))
