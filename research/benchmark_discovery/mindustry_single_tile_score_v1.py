"""Independent exact scorer for one changed-geometry Mindustry placement."""


def score(before, after, plan):
    try:
        target = tuple(plan["target"])
        if len(target) != 2 or any(type(v) is not int for v in target):
            raise ValueError("invalid target")
        required = plan["required"]
        if set(required) != {"block", "team", "rotation"}:
            raise ValueError("invalid required state")
        cost = plan["expected_copper_cost"]
        if type(cost) is not int or cost <= 0:
            raise ValueError("invalid copper cost")
        guard = plan["guard"]
        expected = {(x, y) for y in range(guard["y_min"], guard["y_max"] + 1)
                    for x in range(guard["x_min"], guard["x_max"] + 1)}
        initial = {(row["x"], row["y"]): row for row in before["tiles"]}
        final = {(row["x"], row["y"]): row for row in after["tiles"]}
        if set(initial) != expected or set(final) != expected or target not in expected:
            raise ValueError("guard projection mismatch")
        if initial[target]["block"] != "air":
            raise ValueError("target was not initially empty")
        wrong_target = any(final[target].get(key) != value for key, value in required.items())
        collateral = [list(point) for point in sorted(expected - {target})
                      if final[point] != initial[point]]
        source = tuple(plan["source"])
        source_preserved = final[source] == initial[source] and before["source_item"] == after["source_item"] == "copper"
        core_preserved = (before["core_x"], before["core_y"]) == (after["core_x"], after["core_y"])
        copper_delta = after["copper"] - before["copper"]
        completion = (after["paused"] is True and after["player_dead"] is False and
                      after["unit"]["plans"] == 0 and after["tick"] >= before["tick"])
        satisfied = (not wrong_target and not collateral and source_preserved and
                     core_preserved and copper_delta == -cost and completion)
        return {"status": "VERIFIED" if satisfied else "CONTRADICTED",
                "contract_satisfied": satisfied, "wrong_target": wrong_target,
                "collateral_tiles": collateral, "source_preserved": source_preserved,
                "core_preserved": core_preserved, "copper_delta": copper_delta,
                "paused_idle_completion": completion, "guard_tiles": len(expected),
                "scope": plan["scope"]}
    except (KeyError, TypeError, ValueError, IndexError) as error:
        return {"status": "UNKNOWN", "contract_satisfied": None,
                "reason": str(error), "scope": plan.get("scope") if isinstance(plan, dict) else None}
