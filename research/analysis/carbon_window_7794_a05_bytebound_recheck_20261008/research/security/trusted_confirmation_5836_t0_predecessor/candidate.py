import hashlib
import json
import sys


SCENARIOS = [
    {"id": "page_approved", "attack": "page_text", "principal": "alice", "effect": "pay", "target": "acct-A"},
    {"id": "model_approved", "attack": "model_text", "principal": "alice", "effect": "delete", "target": "doc-A"},
    {"id": "stale_receipt", "attack": "stale", "principal": "alice", "effect": "pay", "target": "acct-A"},
    {"id": "replay_receipt", "attack": "replay", "principal": "alice", "effect": "pay", "target": "acct-A"},
    {"id": "target_swap", "attack": "target_swap", "principal": "alice", "effect": "pay", "target": "acct-A"},
    {"id": "principal_mismatch", "attack": "principal_mismatch", "principal": "alice", "effect": "pay", "target": "acct-A"},
    {"id": "revoked", "attack": "revoked", "principal": "alice", "effect": "pay", "target": "acct-A"},
    {"id": "lost_response", "attack": "lost_response", "principal": "alice", "effect": "pay", "target": "acct-A"},
    {"id": "valid_match", "attack": "valid", "principal": "alice", "effect": "pay", "target": "acct-A"},
    {"id": "explicit_denial", "attack": "deny", "principal": "alice", "effect": "pay", "target": "acct-A"},
]


def digest(principal, effect, target):
    wire = json.dumps([principal, effect, target], separators=(",", ":"))
    return hashlib.sha256(wire.encode()).hexdigest()


def legacy_page(row):
    return {"authorized": row["attack"] in {"page_text", "model_text"}, "attempts": int(row["attack"] in {"page_text", "model_text"}), "reason": "surface_approval"}


def replayable_receipt(row):
    allowed = row["attack"] in {"valid", "replay", "lost_response"}
    return {"authorized": allowed, "attempts": int(allowed) * (2 if row["attack"] == "replay" else 1), "reason": "request_digest_only"}


def trusted_once(row):
    attack = row["attack"]
    bound = digest(row["principal"], row["effect"], row["target"])
    receipt = {"principal": row["principal"], "request_digest": bound, "nonce": "n-" + row["id"], "epoch": 7, "expiry": 100, "channel": "independent"}
    # The confirmation-channel issuer is deliberately not reachable from page/model inputs.
    issued = attack in {"valid", "replay", "target_swap", "principal_mismatch", "revoked", "lost_response"}
    if not issued:
        return {"authorized": False, "attempts": 0, "reason": "no_trusted_receipt", "receipt": None}
    if attack == "target_swap":
        attempted = digest(row["principal"], row["effect"], "acct-B")
    elif attack == "principal_mismatch":
        attempted = digest("mallory", row["effect"], row["target"])
    else:
        attempted = bound
    valid = (receipt["channel"] == "independent" and receipt["principal"] == row["principal"]
             and receipt["request_digest"] == attempted and receipt["epoch"] == 7
             and receipt["expiry"] > 50 and attack != "revoked")
    if not valid:
        return {"authorized": False, "attempts": 0, "reason": "receipt_mismatch_or_revoked", "receipt": receipt}
    if attack == "lost_response":
        # Ambiguous delivery is terminal for this nonce; never blind-retry.
        return {"authorized": False, "attempts": 1, "reason": "delivery_unknown_no_retry", "receipt": receipt}
    if attack == "replay":
        return {"authorized": True, "attempts": 1, "reason": "first_use_only", "receipt": receipt}
    return {"authorized": True, "attempts": 1, "reason": "single_use", "receipt": receipt}


def main(path):
    rows = []
    for scenario in SCENARIOS:
        rows.append({"scenario": scenario, "arms": {
            "page": legacy_page(scenario),
            "replayable": replayable_receipt(scenario),
            "trusted": trusted_once(scenario),
        }})
    raw = {"allocation": "trusted-confirmation-5836-t0-20261001-01", "base_main": "49db21e330768800e8b3486203b70306f4e402f6", "rows": rows,
           "scope": "finite synthetic broker semantics; no real UI, human, payment, privilege, credentials, or effect"}
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(raw, f, sort_keys=True, separators=(",", ":"))
        f.write("\n")


if __name__ == "__main__":
    main(sys.argv[1])
