import copy
import json
import sys
from pathlib import Path


def _reconstruct(fixture):
    expected = []
    for ep in fixture["episodes"]:
        for policy in fixture["policies"]:
            durable = None
            candidate = None
            last_scope = None
            for index, turn in enumerate(ep["turns"]):
                if policy == "static_default":
                    route, choice, asks = "DEFAULT_PROPOSAL", fixture["default"], 0
                elif policy == "clarify_each_turn":
                    choice = turn.get("answer") if turn.get("query_allowed", True) else None
                    if choice not in fixture["choices"]:
                        route, choice, asks = "ASK_YIELD_NO_RESPONSE", None, 1
                    else:
                        route, asks = "ASK_THEN_PROPOSE", 1
                else:
                    if turn["scope"] != last_scope or turn["consent"] is False:
                        durable, candidate = None, None
                    last_scope = turn["scope"]
                    if turn["consent"] is False:
                        route, choice, asks = "DEFAULT_NO_ADAPT_CONSENT", fixture["default"], 0
                    elif durable is not None:
                        route, choice, asks = "ADAPTED_PROPOSAL", durable, 0
                    elif candidate is not None:
                        route, choice, asks = "YIELD_PENDING_CONFIRMATION", None, 0
                    else:
                        route, choice, asks = "DEFAULT_PROPOSAL", fixture["default"], 0

                    action = turn.get("observed_action") if turn["consent"] else None
                    if action not in fixture["choices"]:
                        candidate = None
                    elif durable is not None:
                        if action != durable:
                            durable, candidate = None, action
                        else:
                            candidate = None
                    elif candidate == action:
                        durable, candidate = action, None
                    elif candidate is None:
                        candidate = action
                    else:
                        candidate = None

                expected.append({
                    "episode_id": ep["id"], "tick": index, "policy": policy,
                    "route": route, "proposal": choice,
                    "learned_after": durable if policy == "action_only_adaptive" else None,
                    "pending_after": candidate if policy == "action_only_adaptive" else None,
                    "query_count": asks,
                    "wrong_proposal": choice is not None and choice != turn["target"],
                    "authority_granted": False,
                })
    return expected


def audit(raw, fixture):
    issues = []
    expected = _reconstruct(fixture)
    actual = raw.get("rows")
    if raw.get("schema") != "5749-action-only-raw-a01-v1" or raw.get("allocation") != fixture["allocation"]:
        issues.append("schema_or_allocation")
    if actual != expected:
        issues.append("rows_do_not_match_independent_reconstruction")
    return {"disposition": "PASS_METHOD_SCOPED" if not issues else "FAIL_AUDIT",
            "errors": issues, "rows": len(actual) if isinstance(actual, list) else 0,
            "expected_rows": len(expected)}


def mutations(raw, fixture):
    probes = []
    def probe(name, edit):
        changed = copy.deepcopy(raw)
        edit(changed)
        probes.append({"name": name, "rejected": bool(audit(changed, fixture)["errors"])})
    probe("invent_authority", lambda x: x["rows"][0].update(authority_granted=True))
    probe("adapt_after_one_action", lambda x: next(r for r in x["rows"] if r["policy"] == "action_only_adaptive" and r["episode_id"] == "stable_B" and r["tick"] == 0).update(learned_after="B"))
    probe("retain_after_scope_change", lambda x: next(r for r in x["rows"] if r["policy"] == "action_only_adaptive" and r["episode_id"] == "scope_change" and r["tick"] == 3).update(learned_after="B"))
    probe("retain_after_consent_revoke", lambda x: next(r for r in x["rows"] if r["policy"] == "action_only_adaptive" and r["episode_id"] == "consent_revoked" and r["tick"] == 3).update(learned_after="B"))
    probe("learn_from_absence", lambda x: next(r for r in x["rows"] if r["policy"] == "action_only_adaptive" and r["episode_id"] == "one_off_conflict" and r["tick"] == 2).update(learned_after="A"))
    probe("clarify_memory_leak", lambda x: next(r for r in x["rows"] if r["policy"] == "clarify_each_turn" and r["episode_id"] == "stable_B" and r["tick"] == 1).update(learned_after="B"))
    probe("drop_turn", lambda x: x["rows"].pop())
    return probes


if __name__ == "__main__":
    raw = json.loads(Path(sys.argv[1]).read_text())
    fixture = json.loads(Path(sys.argv[2]).read_text())
    result = audit(raw, fixture)
    result["mutations"] = mutations(raw, fixture)
    if not all(x["rejected"] for x in result["mutations"]):
        result["errors"].append("mutation_escaped")
    result["disposition"] = "PASS_METHOD_SCOPED" if not result["errors"] else "FAIL_AUDIT"
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    raise SystemExit(0 if not result["errors"] else 1)
