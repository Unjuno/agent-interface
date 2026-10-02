"""Independent raw-event reconstruction; does not import candidate functions."""


TERMINAL = {"verified_success", "verified_failure", "policy_safe_stop"}


def reconstruct(episodes, horizons):
    if not episodes or len({e.get("id") for e in episodes}) != len(episodes):
        raise ValueError("cohort identity/denominator invalid")
    if len({e.get("task_contract") for e in episodes}) != 1 or episodes[0].get("task_contract") is None:
        raise ValueError("cohort task contract inconsistent")
    first_types = []
    per_episode = {}
    for episode in episodes:
        launch = episode["launch"]
        events = episode["events"]
        if any(type(e.get("time")) is not int or e["time"] < launch for e in events):
            raise ValueError("invalid event clock")
        if events != sorted(events, key=lambda e: e["time"]):
            raise ValueError("event rows not ordered")
        terminal_rows = [e for e in events if e["type"] in TERMINAL]
        if len(terminal_rows) > 1:
            raise ValueError("competing terminal types are not mutually exclusive")
        first = terminal_rows[0] if terminal_rows else None
        first_types.append(first["type"] if first else None)
        horizon_rows = {}
        for horizon in horizons:
            cutoff = launch + horizon
            success = first if first and first["type"] == "verified_success" else None
            collateral_seen = any(e["type"] == "collateral_observed" and e["time"] <= cutoff
                                  for e in events)
            if collateral_seen:
                state = "COLLATERAL_OBSERVED"
            elif not success or success["time"] > cutoff:
                state = "NO_VERIFIED_SUCCESS_BY_HORIZON"
            else:
                lost = next((e for e in events if e["type"] == "followup_lost"), None)
                complete = next((e for e in events if e["type"] == "followup_complete"), None)
                if (complete and complete["time"] >= cutoff) or (lost and lost["time"] > cutoff):
                    state = "NO_COLLATERAL_COMPLETE"
                elif lost and lost["time"] <= cutoff:
                    state = "FOLLOWUP_UNKNOWN"
                else:
                    state = "FOLLOWUP_PENDING"
            horizon_rows[str(horizon)] = {"cutoff": cutoff, "status": state}
        per_episode[episode["id"]] = {
            "first_terminal_type": first["type"] if first else None,
            "first_terminal_time": first["time"] if first else None,
            "horizons": horizon_rows,
        }

    n = len(episodes)
    counts = {kind: first_types.count(kind) for kind in sorted(TERMINAL)}
    summaries = {}
    for horizon in horizons:
        states = [per_episode[e["id"]]["horizons"][str(horizon)]["status"] for e in episodes]
        lower = states.count("NO_COLLATERAL_COMPLETE")
        upper = lower + states.count("FOLLOWUP_UNKNOWN") + states.count("FOLLOWUP_PENDING")
        summaries[str(horizon)] = {
            "cutoff_from_launch": horizon,
            "states": {state: states.count(state) for state in sorted(set(states))},
            "all_launched_n": n,
            "clean_lower_n": lower,
            "clean_upper_n": upper,
            "clean_lower_fraction": lower / n,
            "clean_upper_fraction": upper / n,
        }
    success_n = counts["verified_success"]
    return {
        "all_launched_n": n,
        "first_terminal_counts": counts,
        "first_terminal_success_n": success_n,
        "first_terminal_success_fraction": success_n / n,
        "horizons": summaries,
        "episodes": [{"episode_id": e["id"], **per_episode[e["id"]]} for e in episodes],
    }


def audit(fixture, result):
    expected = reconstruct(fixture["episodes"], fixture["horizons_from_launch"])
    errors = []
    for key, value in expected.items():
        actual = result.get(key)
        if actual != value:
            errors.append(f"{key} differs from independent event reconstruction")
    if result.get("schema") != "post-success-collateral-candidate-v1":
        errors.append("candidate schema missing")
    return {"schema": "post-success-collateral-audit-v1",
            "status": "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD_SCOPED",
            "errors": errors,
            "reconstructed_episodes": expected["all_launched_n"],
            "reconstructed_horizon_rows": expected["all_launched_n"] * len(fixture["horizons_from_launch"]),
            "candidate_and_auditor_separate": True,
            "auditor_invocations": 1,
            "retries": 0}


def main():
    import argparse
    import json
    from pathlib import Path
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(here / "fixture.json"))
    parser.add_argument("--candidate", default=str(here / "candidate_result.json"))
    parser.add_argument("--output", default=str(here / "audit_result.json"))
    args = parser.parse_args()
    fixture = json.loads(Path(args.input).read_text(encoding="utf-8"))
    result = json.loads(Path(args.candidate).read_text(encoding="utf-8"))
    audited = audit(fixture, result)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(audited, sort_keys=True, indent=2) + "\n",
                                 encoding="utf-8")
    print(json.dumps(audited, sort_keys=True))
    raise SystemExit(0 if audited["status"] == "PASS_METHOD_SCOPED" else 1)


if __name__ == "__main__":
    main()
