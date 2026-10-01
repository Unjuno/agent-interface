import json
import sys


def evaluate(fixture, intervention):
    entries = fixture["disturbances"]
    refined = intervention["observation_refinement"]
    extra_response = intervention["added_response"]
    response_latency = intervention.get("added_latency_ms", 0)
    rows = []
    groups = {}
    for item in entries:
        observed = item["observation"]
        if refined:
            observed += "::" + item["disturbance_id"]
        response = extra_response if extra_response == item["required_response"] else item["available_response"]
        latency = (response_latency if "added_latency_ms" in intervention else item["latency_ms"]) if response == extra_response and extra_response else item["latency_ms"]
        authorized = item["authority"] and response == item["required_response"]
        timely = latency <= fixture["deadline_ms"]
        outcome = "COVERED" if authorized and timely else ("AUTHORITY_GAP" if not item["authority"] and response == item["required_response"] else ("DEADLINE_GAP" if authorized and not timely else "NO_RESPONSE"))
        row = {"disturbance_id": item["disturbance_id"], "observation": observed,
               "required_response": item["required_response"], "chosen_response": response,
               "authority": item["authority"], "latency_ms": latency,
               "authorized": authorized, "timely": timely, "outcome": outcome}
        rows.append(row)
        groups.setdefault(observed, []).append(row)
    alias = any(len({r["required_response"] for r in group}) > 1 for group in groups.values())
    if alias:
        classification = "OBSERVATION_ALIAS"
    elif any(r["outcome"] == "DEADLINE_GAP" for r in rows):
        classification = "DEADLINE_GAP"
    elif any(r["outcome"] == "AUTHORITY_GAP" for r in rows):
        classification = "AUTHORITY_GAP"
    elif all(r["outcome"] == "COVERED" for r in rows):
        classification = "COVERED"
    else:
        classification = "UNCOVERED"
    return {"classification": classification, "disturbances": rows,
            "observation_alias_groups": [[r["disturbance_id"] for r in g] for g in groups.values() if len({r["required_response"] for r in g}) > 1]}


def main():
    fixture = json.load(sys.stdin)
    result = {"baseline": evaluate(fixture, {"observation_refinement": False, "added_response": None}),
              "extra_verifier": evaluate(fixture, fixture["interventions"]["extra_verifier"])}
    for name in ("added_observation", "added_recovery", "forbidden_response", "deadline_gap"):
        result[name] = evaluate(fixture, fixture["interventions"][name])
    result["combined"] = evaluate(fixture, fixture["interventions"]["combined"])
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
