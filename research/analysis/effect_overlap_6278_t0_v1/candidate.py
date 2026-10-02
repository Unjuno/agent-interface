import argparse
import json
from pathlib import Path


def run(fixture):
    rows = []
    for scenario in fixture["scenarios"]:
        used = {name: 0 for name in fixture["routes"]}
        for task in scenario["tasks"]:
            options = []
            for name, route in fixture["routes"].items():
                edges = route["edges"]
                if edges.get(task["class"]) is not True:
                    continue
                if task.get("authorized", True) is not True:
                    continue
                if task["effect_truth"] != "exact":
                    continue
                if set(route["dependencies"]) & set(scenario["lost"]):
                    continue
                if used[name] >= route["capacity"]:
                    continue
                done = max(task["release_ms"], scenario["reconfigure_ms"] + route["ready_ms"]) + route["effect_ms"]
                if done <= task["deadline_ms"]:
                    options.append((done, route["cost"], name))
            if options:
                done, _, chosen = min(options)
                used[chosen] += 1
                rows.append({"scenario": scenario["id"], "task": task["id"], "route": chosen, "completion_ms": done, "status": "EXACT_ON_TIME"})
            else:
                rows.append({"scenario": scenario["id"], "task": task["id"], "route": None, "completion_ms": None, "status": "ABSTAIN"})
    return {"schema": "effect-overlap-raw-v1", "rows": rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", default=str(Path(__file__).with_name("fixture.json")))
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    fixture = json.loads(Path(args.fixture).read_text())
    Path(args.out).write_text(json.dumps(run(fixture), indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
