import hashlib
import json
import sys


IDS = ["page_approved", "model_approved", "stale_receipt", "replay_receipt", "target_swap", "principal_mismatch", "revoked", "lost_response", "valid_match", "explicit_denial"]
SCENARIOS = [
    {"id": name, "attack": attack, "principal": "alice", "effect": effect, "target": target}
    for name, attack, effect, target in [
        ("page_approved", "page_text", "pay", "acct-A"), ("model_approved", "model_text", "delete", "doc-A"),
        ("stale_receipt", "stale", "pay", "acct-A"), ("replay_receipt", "replay", "pay", "acct-A"),
        ("target_swap", "target_swap", "pay", "acct-A"), ("principal_mismatch", "principal_mismatch", "pay", "acct-A"),
        ("revoked", "revoked", "pay", "acct-A"), ("lost_response", "lost_response", "pay", "acct-A"),
        ("valid_match", "valid", "pay", "acct-A"), ("explicit_denial", "deny", "pay", "acct-A"),
    ]
]


def digest(principal, effect, target):
    return hashlib.sha256(json.dumps([principal, effect, target], separators=(",", ":")).encode()).hexdigest()


def process(rows):
    used_nonces = {"n-replay_receipt"}  # This fixture's replay token was consumed before the observed request.
    out = []
    for row in rows:
        name, attack = row["id"], row["attack"]
        page_ok = attack in {"page_text", "model_text"}
        # Request-bound receipt validates principal/effect/target/revocation; it is intentionally replayable.
        replayable_ok = attack in {"replay", "lost_response", "valid"}
        replayable_attempts = 2 if attack in {"replay", "lost_response"} else int(replayable_ok)
        page = {"authorized": page_ok, "attempts": int(page_ok), "reason": "surface_approval"}
        replayable = {"authorized": replayable_ok, "attempts": replayable_attempts, "reason": "request_bound_replayable"}
        nonce = "n-" + name
        rec = {"channel": "independent", "principal": row["principal"], "request_digest": digest(row["principal"], row["effect"], row["target"]), "nonce": nonce, "epoch": 7, "expiry": 10 if attack == "stale" else 100}
        emitted = attack in {"stale", "replay", "target_swap", "principal_mismatch", "revoked", "lost_response", "valid"}
        if not emitted:
            trusted = {"authorized": False, "attempts": 0, "reason": "no_trusted_receipt", "receipt": None}
        else:
            target_digest = digest(row["principal"], row["effect"], "acct-B") if attack == "target_swap" else rec["request_digest"]
            principal = "mallory" if attack == "principal_mismatch" else rec["principal"]
            checks = (principal == row["principal"] and target_digest == rec["request_digest"]
                      and rec["epoch"] == 7 and rec["expiry"] > 50 and attack != "revoked")
            if not checks:
                trusted = {"authorized": False, "attempts": 0, "reason": "binding_expiry_or_revocation", "receipt": rec}
            elif nonce in used_nonces:
                trusted = {"authorized": False, "attempts": 0, "reason": "nonce_already_consumed", "receipt": rec}
            else:
                used_nonces.add(nonce)  # Consume before attempting; unknown delivery remains non-replayable.
                if attack == "lost_response":
                    trusted = {"authorized": False, "attempts": 1, "reason": "delivery_unknown_no_retry", "receipt": rec}
                else:
                    trusted = {"authorized": True, "attempts": 1, "reason": "single_use", "receipt": rec}
        out.append({"scenario": row, "arms": {"page": page, "replayable": replayable, "trusted": trusted}})
    return out


def main(path):
    raw = {"allocation": "trusted-confirmation-5836-t0-successor-20261001-01", "base_main": "45395880f873f1592bc188a37471d8380535e1ec", "rows": process(SCENARIOS), "scope": "finite synthetic broker semantics only"}
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(raw, f, sort_keys=True, separators=(",", ":")); f.write("\n")


if __name__ == "__main__":
    main(sys.argv[1])
