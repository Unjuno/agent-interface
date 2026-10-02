import json
import pathlib
import sys


def rebuild(items, deadline, intervention):
    groups = {}
    rows = []
    for d in items:
        response = intervention["added_response"] if d["required_response"] == intervention["added_response"] else d["available_response"]
        latency = d["latency_ms"]
        if response == intervention["added_response"] and intervention["added_response"]:
            latency = intervention.get("added_latency_ms", latency)
        authorized = d["authority"] and response == d["required_response"]
        timely = latency <= deadline
        if response == d["required_response"] and not d["authority"]:
            outcome = "AUTHORITY_GAP"
        elif not authorized:
            outcome = "NO_RESPONSE"
        elif not timely:
            outcome = "DEADLINE_GAP"
        else:
            outcome = "COVERED"
        obs = d["observation"]
        if intervention["observation_refinement"]:
            obs = obs + "::" + d["disturbance_id"]
        row = {"disturbance_id": d["disturbance_id"], "observation": obs,
               "required_response": d["required_response"], "chosen_response": response,
               "authority": d["authority"], "latency_ms": latency,
               "authorized": authorized, "timely": timely, "outcome": outcome}
        rows.append(row)
        groups.setdefault(obs, []).append(d)
    aliases = [[d["disturbance_id"] for d in group] for group in groups.values()
               if len({d["required_response"] for d in group}) > 1]
    outcomes = {row["outcome"] for row in rows}
    if aliases:
        label = "OBSERVATION_ALIAS"
    elif "DEADLINE_GAP" in outcomes:
        label = "DEADLINE_GAP"
    elif "AUTHORITY_GAP" in outcomes:
        label = "AUTHORITY_GAP"
    elif outcomes == {"COVERED"}:
        label = "COVERED"
    else:
        label = "UNCOVERED"
    return {"classification": label, "disturbances": rows, "observation_alias_groups": aliases}


def oracle(fixture):
    interventions = fixture["interventions"]
    baseline = {"observation_refinement": False, "added_response": None}
    return {"baseline": rebuild(fixture["disturbances"], fixture["deadline_ms"], baseline),
            "extra_verifier": rebuild(fixture["disturbances"], fixture["deadline_ms"], interventions["extra_verifier"]),
            **{name: rebuild(fixture["disturbances"], fixture["deadline_ms"], interventions[name])
               for name in ("added_observation", "added_recovery", "forbidden_response", "deadline_gap", "combined")}}


def main():
    actual = json.load(sys.stdin)
    fixture = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    expected = oracle(fixture)
    if actual != expected:
        raise SystemExit("FAIL: independent finite-state reconstruction mismatch")
    ids = [d["disturbance_id"] for d in fixture["disturbances"]]
    for arm in expected.values():
        if [r["disturbance_id"] for r in arm["disturbances"]] != ids:
            raise SystemExit("FAIL: offered disturbance denominator mismatch")
    print(json.dumps({"audit": "PASS_METHOD_SCOPED", "interventions": len(expected),
                      "offered_disturbances_per_intervention": len(ids), "errors": []}, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
