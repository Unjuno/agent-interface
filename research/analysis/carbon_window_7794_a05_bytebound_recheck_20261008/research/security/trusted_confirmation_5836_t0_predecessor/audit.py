import copy
import hashlib
import json
import sys


IDS = ["page_approved", "model_approved", "stale_receipt", "replay_receipt", "target_swap", "principal_mismatch", "revoked", "lost_response", "valid_match", "explicit_denial"]
NEGATIVE = set(IDS[:8]) | {"explicit_denial"}


def expected(row):
    name = row["scenario"]["id"]
    page = name in {"page_approved", "model_approved"}
    replayable = name in {"replay_receipt", "lost_response", "target_swap", "principal_mismatch", "revoked", "valid_match"}
    if name == "lost_response":
        replayable = True
    trusted_attempts = 1 if name == "lost_response" else 0
    trusted = name == "valid_match"
    why = "single_use" if trusted else ("delivery_unknown_no_retry" if name == "lost_response" else "refused")
    return {
        "page": (page, int(page)),
        "replayable": (replayable, 2 if name == "replay_receipt" else int(replayable)),
        "trusted": (trusted, trusted_attempts + int(trusted)),
        "trusted_reason": why,
    }


def validate(raw):
    errors = []
    rows = raw.get("rows")
    if raw.get("allocation") != "trusted-confirmation-5836-t0-20261001-01": errors.append("allocation")
    if not isinstance(rows, list) or [x.get("scenario", {}).get("id") for x in rows] != IDS:
        return errors + ["scenario_order_or_count"]
    for item in rows:
        scenario = item["scenario"]
        e = expected(item)
        for arm in ("page", "replayable", "trusted"):
            result = item.get("arms", {}).get(arm, {})
            if (result.get("authorized"), result.get("attempts")) != e[arm]: errors.append("decision:" + scenario["id"] + ":" + arm)
        if item["arms"]["trusted"].get("reason") != e["trusted_reason"]: errors.append("reason:" + scenario["id"])
        if scenario["id"] in NEGATIVE and item["arms"]["trusted"].get("authorized"): errors.append("unauthorized_effect:" + scenario["id"])
    if sum(x["arms"]["trusted"]["authorized"] for x in rows) != 1: errors.append("valid_control_count")
    if rows[7]["arms"]["trusted"].get("attempts") != 1: errors.append("lost_response_must_not_retry")
    return errors


def controls(raw):
    out = []
    mutations = [
        ("authorize_page_forgery", lambda x: x["rows"][0]["arms"]["trusted"].update(authorized=True)),
        ("drop_denial_case", lambda x: x["rows"].pop()),
        ("duplicate_replay_effect", lambda x: x["rows"][3]["arms"]["trusted"].update(attempts=2)),
        ("authorize_revoked", lambda x: x["rows"][6]["arms"]["trusted"].update(authorized=True)),
        ("blind_retry_unknown", lambda x: x["rows"][7]["arms"]["trusted"].update(attempts=2)),
    ]
    for name, mutate in mutations:
        changed = copy.deepcopy(raw)
        mutate(changed)
        errors = validate(changed)
        out.append({"name": name, "rejected": bool(errors), "errors": errors})
    return out


def main(path):
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    errors = validate(raw)
    c = controls(raw)
    if not all(x["rejected"] for x in c): errors.append("mutation_control_survived")
    print(json.dumps({"decision": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT", "rows": len(raw.get("rows", [])), "errors": errors, "mutation_controls": c}, sort_keys=True, separators=(",", ":")))
    raise SystemExit(bool(errors))


if __name__ == "__main__":
    main(sys.argv[1])
