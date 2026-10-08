import copy
import json
import sys


IDS = ["page_approved", "model_approved", "stale_receipt", "replay_receipt", "target_swap", "principal_mismatch", "revoked", "lost_response", "valid_match", "explicit_denial"]


def validate(raw):
    errors = []
    rows = raw.get("rows")
    if raw.get("allocation") != "trusted-confirmation-5836-t0-successor-20261001-01": errors.append("allocation")
    if not isinstance(rows, list) or [r.get("scenario", {}).get("id") for r in rows] != IDS: return errors + ["row_identity"]
    for item in rows:
        name = item["scenario"]["id"]
        arms = item.get("arms", {})
        exp_page = name in {"page_approved", "model_approved"}
        exp_replay = name in {"replay_receipt", "lost_response", "valid_match"}
        exp_replay_n = 2 if name in {"replay_receipt", "lost_response"} else int(exp_replay)
        exp_trusted = name == "valid_match"
        exp_attempts = 1 if name in {"valid_match", "lost_response"} else 0
        exp_reason = ("single_use" if exp_trusted else "delivery_unknown_no_retry" if name == "lost_response"
                      else "nonce_already_consumed" if name == "replay_receipt"
                      else "binding_expiry_or_revocation" if name in {"stale_receipt", "target_swap", "principal_mismatch", "revoked"}
                      else "no_trusted_receipt")
        expectations = {"page": (exp_page, int(exp_page)), "replayable": (exp_replay, exp_replay_n), "trusted": (exp_trusted, exp_attempts)}
        for arm, (auth, attempts) in expectations.items():
            result = arms.get(arm, {})
            if (result.get("authorized"), result.get("attempts")) != (auth, attempts): errors.append(f"decision:{name}:{arm}")
        if arms.get("trusted", {}).get("reason") != exp_reason: errors.append(f"reason:{name}")
        if name != "valid_match" and arms.get("trusted", {}).get("authorized"): errors.append(f"unauthorized:{name}")
    return errors


def main(path):
    with open(path, encoding="utf-8") as f: raw = json.load(f)
    errors = validate(raw)
    controls = []
    mutations = [
        ("forge_page", lambda x: x["rows"][0]["arms"]["trusted"].update(authorized=True)),
        ("authorize_replay", lambda x: x["rows"][3]["arms"]["trusted"].update(authorized=True, attempts=1)),
        ("swap_effect", lambda x: x["rows"][4]["arms"]["trusted"].update(authorized=True)),
        ("restore_revoked", lambda x: x["rows"][6]["arms"]["trusted"].update(authorized=True)),
        ("retry_unknown", lambda x: x["rows"][7]["arms"]["trusted"].update(attempts=2)),
    ]
    for name, fn in mutations:
        changed = copy.deepcopy(raw); fn(changed); e = validate(changed)
        controls.append({"name": name, "rejected": bool(e), "errors": e})
    if not all(c["rejected"] for c in controls): errors.append("mutation_survived")
    print(json.dumps({"decision": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT", "rows": len(raw.get("rows", [])), "errors": errors, "mutation_controls": controls}, sort_keys=True, separators=(",", ":")))
    raise SystemExit(bool(errors))


if __name__ == "__main__": main(sys.argv[1])
