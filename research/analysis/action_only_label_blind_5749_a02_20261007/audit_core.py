"""Independent reconstruction and mutation checks; does not import candidate/scorer."""

import copy
import hashlib
import json

ALLOCATION = "5749-ACTION-ONLY-LABEL-BLIND-A02-20261007"
POLICIES = ("static_default", "clarify_each_turn", "action_only_adaptive")


def _rows(policy_input):
    expected = []
    for episode in policy_input["episodes"]:
        for policy in POLICIES:
            durable = candidate = None
            last_scope = None
            for index, turn in enumerate(episode["turns"]):
                asks = 0
                if policy == "static_default":
                    route, choice = "DEFAULT_PROPOSAL", policy_input["default"]
                elif policy == "clarify_each_turn":
                    asks = 1
                    answer = turn["answer"] if turn["query_allowed"] else None
                    if answer in policy_input["choices"]:
                        route, choice = "ASK_THEN_PROPOSE", answer
                    else:
                        route, choice = "ASK_YIELD_NO_RESPONSE", None
                else:
                    if last_scope != turn["scope"] or turn["consent"] is False:
                        durable = candidate = None
                    last_scope = turn["scope"]
                    if turn["consent"] is False:
                        route, choice = "DEFAULT_NO_ADAPT_CONSENT", policy_input["default"]
                    elif durable is not None:
                        route, choice = "ADAPTED_PROPOSAL", durable
                    elif candidate is not None:
                        route, choice = "YIELD_PENDING_CONFIRMATION", None
                    else:
                        route, choice = "DEFAULT_PROPOSAL", policy_input["default"]
                    action = turn["observed_action"] if turn["consent"] else None
                    if action not in policy_input["choices"]:
                        candidate = None
                    elif durable is None:
                        if candidate == action:
                            durable, candidate = action, None
                        elif candidate is None:
                            candidate = action
                        else:
                            candidate = None
                    elif action != durable:
                        durable, candidate = None, action
                    else:
                        candidate = None
                expected.append({
                    "episode_id": episode["id"], "tick": index, "policy": policy,
                    "route": route, "proposal": choice,
                    "learned_after": durable if policy == "action_only_adaptive" else None,
                    "pending_after": candidate if policy == "action_only_adaptive" else None,
                    "query_count": asks, "authority_granted": False,
                })
    return expected


def _scores(rows, key):
    truth = {(x["episode_id"], x["tick"]): x["target"] for x in key["targets"]}
    output = []
    summary = {name: {"proposals": 0, "correct": 0, "wrong": 0, "yields": 0, "queries": 0}
               for name in POLICIES}
    for row in rows:
        target = truth[(row["episode_id"], row["tick"])]
        choice = row["proposal"]
        outcome = "YIELD" if choice is None else "MATCH" if choice == target else "MISMATCH"
        output.append({"episode_id": row["episode_id"], "tick": row["tick"],
                       "policy": row["policy"], "target": target,
                       "proposal": choice, "outcome": outcome})
        item = summary[row["policy"]]
        item["queries"] += row["query_count"]
        if choice is None:
            item["yields"] += 1
        else:
            item["proposals"] += 1
            item["correct" if outcome == "MATCH" else "wrong"] += 1
    return {"schema": "5749-a02-score-v1", "allocation": ALLOCATION,
            "rows": output, "summary": summary}


def _check(policy_input, key, raw, score, freeze, code_dir):
    errors = []
    if hashlib.sha256(freeze["policy_input_bytes"]).hexdigest() != freeze["policy_input_sha256"]:
        errors.append("policy_freeze_hash")
    if hashlib.sha256(freeze["scoring_key_bytes"]).hexdigest() != freeze["scoring_key_sha256"]:
        errors.append("scoring_key_freeze_hash")
    if key != json.loads(freeze["scoring_key_bytes"]):
        errors.append("scoring_key_content_changed")
    if policy_input.get("schema") != "5749-a02-policy-input-v1" or policy_input.get("allocation") != ALLOCATION:
        errors.append("policy_identity")
    if set(policy_input) != {"schema", "allocation", "choices", "default", "policies", "episodes"}:
        errors.append("policy_field_set")
    if any("target" in turn or "preference_label" in turn
           for episode in policy_input.get("episodes", []) for turn in episode.get("turns", [])):
        errors.append("label_leak_in_policy_input")
    choices = policy_input.get("choices", [])
    if (key.get("schema") != "5749-a02-scoring-key-v1"
            or any(row.get("target") not in choices for row in key.get("targets", []))):
        errors.append("scoring_key_domain")
    for name, expected_hash in freeze.get("code_sha256", {}).items():
        try:
            actual = hashlib.sha256((code_dir / name).read_bytes()).hexdigest()
        except OSError:
            actual = None
        if actual != expected_hash:
            errors.append("code_hash:" + name)
    expected_rows = _rows(policy_input)
    if raw != {"schema": "5749-a02-policy-output-v1", "allocation": ALLOCATION, "rows": expected_rows}:
        errors.append("candidate_rows_mismatch")
    expected_score = _scores(expected_rows, key)
    if score != expected_score:
        errors.append("score_rows_or_summary_mismatch")
    if raw.get("rows") and any(row.get("authority_granted") is not False for row in raw["rows"]):
        errors.append("authority_changed")
    return errors


def audit(policy_input, key, raw, score, freeze, code_dir):
    errors = _check(policy_input, key, raw, score, freeze, code_dir)
    controls = []
    for name, mutate in (
        ("raw_authority", lambda x: x["rows"][0].update(authority_granted=True)),
        ("raw_wrong_proposal", lambda x: x["rows"][0].update(proposal="B")),
        ("raw_missing_row", lambda x: x["rows"].pop()),
        ("raw_injected_target", lambda x: x["rows"][0].update(target="B")),
    ):
        altered = copy.deepcopy(raw)
        mutate(altered)
        controls.append({"name": name, "rejected": bool(_check(policy_input, key, altered, score, freeze, code_dir))})
    altered_score = copy.deepcopy(score)
    altered_score["rows"][0]["outcome"] = "MATCH"
    controls.append({"name": "score_outcome", "rejected": bool(_check(policy_input, key, raw, altered_score, freeze, code_dir))})
    changed_key = copy.deepcopy(key)
    changed_key["targets"][0]["target"] = "A" if changed_key["targets"][0]["target"] != "A" else "B"
    controls.append({"name": "score_key_mutation",
                     "rejected": bool(_check(policy_input, changed_key, raw, score, freeze, code_dir))})
    rejected = sum(x["rejected"] for x in controls)
    if rejected != len(controls):
        errors.append("mutation_control_escaped")
    return {"disposition": "PASS_LABEL_BLIND_METHOD_SCOPED" if not errors else "FAIL_AUDIT",
            "errors": errors, "rows": len(raw.get("rows", [])),
            "raw_mutations_rejected": sum(x["rejected"] for x in controls if x["name"].startswith("raw_")),
            "score_mutations_rejected": sum(x["rejected"] for x in controls if x["name"].startswith("score_")),
            "mutation_controls": controls}
