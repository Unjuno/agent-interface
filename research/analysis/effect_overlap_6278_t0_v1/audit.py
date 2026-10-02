import argparse
import json
from pathlib import Path


def expected(fixture):
    result = {}
    for scenario in fixture["scenarios"]:
        capacity = {key: value["capacity"] for key, value in fixture["routes"].items()}
        for task in scenario["tasks"]:
            eligible = []
            for key in sorted(fixture["routes"]):
                route = fixture["routes"][key]
                if task["class"] not in route["edges"] or route["edges"][task["class"]] is not True:
                    continue
                if task.get("authorized", True) is not True or task["effect_truth"] != "exact":
                    continue
                if any(dep in scenario["lost"] for dep in route["dependencies"]):
                    continue
                if capacity[key] < 1:
                    continue
                finish = max(task["release_ms"], scenario["reconfigure_ms"] + route["ready_ms"]) + route["effect_ms"]
                if finish > task["deadline_ms"]:
                    continue
                eligible.append((finish, route["cost"], key))
            if eligible:
                finish, _, selected = min(eligible)
                capacity[selected] -= 1
                result[(scenario["id"], task["id"])] = ("EXACT_ON_TIME", selected, finish)
            else:
                result[(scenario["id"], task["id"])] = ("ABSTAIN", None, None)
    return result


def audit(fixture, raw):
    exp = expected(fixture)
    errors = []
    observed = {}
    for row in raw.get("rows", []):
        key = (row.get("scenario"), row.get("task"))
        if key in observed:
            errors.append("duplicate_task_row:" + repr(key))
        observed[key] = (row.get("status"), row.get("route"), row.get("completion_ms"))
    if set(observed) != set(exp):
        errors.append("task_denominator_mismatch")
    for key, value in exp.items():
        if observed.get(key) != value:
            errors.append("oracle_mismatch:" + repr(key))
    return {"schema": "effect-overlap-audit-v1", "expected_rows": len(exp), "observed_rows": len(observed), "errors": errors, "disposition": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT_GATE"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("raw")
    parser.add_argument("--fixture", default=str(Path(__file__).with_name("fixture.json")))
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    result = audit(json.loads(Path(args.fixture).read_text()), json.loads(Path(args.raw).read_text()))
    Path(args.out).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    if result["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
