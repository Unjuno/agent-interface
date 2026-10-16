import json
import sys
from pathlib import Path


def run(fixture):
    rows = []
    for episode in fixture["episodes"]:
        for policy in fixture["policies"]:
            learned = None
            pending = None
            scope = None
            for tick, event in enumerate(episode["turns"]):
                if policy == "static_default":
                    route, proposal, query_count = "DEFAULT_PROPOSAL", fixture["default"], 0
                elif policy == "clarify_each_turn":
                    answer = event.get("answer") if event.get("query_allowed", True) else None
                    if answer in fixture["choices"]:
                        route, proposal, query_count = "ASK_THEN_PROPOSE", answer, 1
                    else:
                        route, proposal, query_count = "ASK_YIELD_NO_RESPONSE", None, 1
                else:
                    if scope != event["scope"] or not event["consent"]:
                        learned = pending = None
                    scope = event["scope"]
                    if not event["consent"]:
                        route, proposal, query_count = "DEFAULT_NO_ADAPT_CONSENT", fixture["default"], 0
                    elif learned in fixture["choices"]:
                        route, proposal, query_count = "ADAPTED_PROPOSAL", learned, 0
                    elif pending is not None:
                        route, proposal, query_count = "YIELD_PENDING_CONFIRMATION", None, 0
                    else:
                        route, proposal, query_count = "DEFAULT_PROPOSAL", fixture["default"], 0

                    observation = event.get("observed_action") if event["consent"] else None
                    if observation not in fixture["choices"]:
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
                    "query_count": query_count,
                    "wrong_proposal": proposal is not None and proposal != event["target"],
                    "authority_granted": False,
                })
    return {"schema": "5749-action-only-raw-a01-v1",
            "allocation": fixture["allocation"], "rows": rows}


if __name__ == "__main__":
    fixture_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("fixture.json")
    print(json.dumps(run(json.loads(fixture_path.read_text())), sort_keys=True,
                     separators=(",", ":")))
