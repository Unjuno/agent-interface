"""Emit proposals using only a frozen policy-input file, never preference labels."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

SCHEMA = "5749-a02-policy-input-v1"
OUTPUT_SCHEMA = "5749-a02-policy-output-v1"
ALLOCATION = "5749-ACTION-ONLY-LABEL-BLIND-A02-20261007"
POLICIES = ("static_default", "clarify_each_turn", "action_only_adaptive")


def validate(data):
    if set(data) != {"schema", "allocation", "choices", "default", "policies", "episodes"}:
        raise ValueError("unexpected_policy_field_or_missing_field")
    if data["schema"] != SCHEMA or data["allocation"] != ALLOCATION:
        raise ValueError("policy_identity")
    choices = data["choices"]
    if (not isinstance(choices, list) or len(choices) < 2
            or any(not isinstance(x, str) or not x for x in choices)
            or len(set(choices)) != len(choices) or data["default"] not in choices
            or data["policies"] != list(POLICIES)):
        raise ValueError("policy_domain")
    episode_ids = set()
    for episode in data["episodes"]:
        if set(episode) != {"id", "turns"} or not episode["id"] or episode["id"] in episode_ids:
            raise ValueError("episode_schema_or_identity")
        episode_ids.add(episode["id"])
        for turn in episode["turns"]:
            if set(turn) != {"scope", "consent", "observed_action", "answer", "query_allowed"}:
                raise ValueError("unexpected_policy_field_or_missing_field")
            if (not isinstance(turn["scope"], str) or type(turn["consent"]) is not bool
                    or type(turn["query_allowed"]) is not bool
                    or turn["observed_action"] is not None and turn["observed_action"] not in choices
                    or turn["answer"] is not None and turn["answer"] not in choices):
                raise ValueError("turn_domain")
    return data


def run(data):
    validate(data)
    rows = []
    for episode in data["episodes"]:
        for policy in POLICIES:
            learned = pending = None
            prior_scope = None
            for tick, event in enumerate(episode["turns"]):
                query_count = 0
                if policy == "static_default":
                    route, proposal = "DEFAULT_PROPOSAL", data["default"]
                elif policy == "clarify_each_turn":
                    query_count = 1
                    answer = event["answer"] if event["query_allowed"] else None
                    if answer in data["choices"]:
                        route, proposal = "ASK_THEN_PROPOSE", answer
                    else:
                        route, proposal = "ASK_YIELD_NO_RESPONSE", None
                else:
                    if prior_scope != event["scope"] or not event["consent"]:
                        learned = pending = None
                    prior_scope = event["scope"]
                    if not event["consent"]:
                        route, proposal = "DEFAULT_NO_ADAPT_CONSENT", data["default"]
                    elif learned is not None:
                        route, proposal = "ADAPTED_PROPOSAL", learned
                    elif pending is not None:
                        route, proposal = "YIELD_PENDING_CONFIRMATION", None
                    else:
                        route, proposal = "DEFAULT_PROPOSAL", data["default"]

                    observation = event["observed_action"] if event["consent"] else None
                    if observation not in data["choices"]:
                        pending = None
                    elif learned is None:
                        if pending == observation:
                            learned, pending = observation, None
                        elif pending is not None:
                            pending = None
                        else:
                            pending = observation
                    elif observation != learned:
                        learned, pending = None, observation
                    else:
                        pending = None

                rows.append({
                    "episode_id": episode["id"], "tick": tick, "policy": policy,
                    "route": route, "proposal": proposal,
                    "learned_after": learned if policy == "action_only_adaptive" else None,
                    "pending_after": pending if policy == "action_only_adaptive" else None,
                    "query_count": query_count, "authority_granted": False,
                })
    return {"schema": OUTPUT_SCHEMA, "allocation": ALLOCATION, "rows": rows}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", default=str(Path(__file__).with_name("FREEZE.json")))
    parser.add_argument("policy_input")
    parser.add_argument("raw_output")
    args = parser.parse_args(argv)
    try:
        data = json.loads(Path(args.policy_input).read_text())
        validate(data)
        expected_hash = json.loads(Path(args.freeze).read_text())["policy_input_sha256"]
        if hashlib.sha256(Path(args.policy_input).read_bytes()).hexdigest() != expected_hash:
            raise ValueError("policy_input_hash_mismatch")
        output = run(data)
        Path(args.raw_output).write_text(json.dumps(output, sort_keys=True, indent=2) + "\n")
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
