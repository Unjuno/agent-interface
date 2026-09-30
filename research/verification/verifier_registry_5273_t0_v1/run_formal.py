"""Single deterministic invocation against frozen JSON; emits retained raw."""
import hashlib
import json
from pathlib import Path

from candidate import preflight

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    freeze = json.loads((HERE / "FREEZE.json").read_text())
    for name, expected in freeze["formal_source_sha256"].items():
        if sha(HERE / name) != expected:
            raise SystemExit(f"frozen input changed: {name}")
    cases = json.loads((HERE / "cases.json").read_text())
    registry = json.loads((HERE / "registry.json").read_text())
    decisions = []
    for item in cases["cases"]:
        result = preflight({"schema": "verifier_plan.v0.1", "checks": [item["check"]]}, registry, cases["resources"])
        decisions.extend(result["decisions"])
    raw = {
        "schema": "verifier_registry_5273_raw.v1",
        "allocation": freeze["allocation"],
        "base_commit": freeze["base_commit"],
        "freeze_sha256": sha(HERE / "FREEZE.json"),
        "registry_sha256": sha(HERE / "registry.json"),
        "cases_sha256": sha(HERE / "cases.json"),
        "candidate_sha256": sha(HERE / "candidate.py"),
        "decisions": decisions,
    }
    out = HERE / "results" / "host-construction-01"
    out.mkdir(parents=True, exist_ok=False)
    payload = json.dumps(raw, sort_keys=True, indent=2) + "\n"
    (out / "RAW.json").write_text(payload)
    (out / "runner.stdout.txt").write_text(json.dumps({"status": "EXECUTED_HOST_CONSTRUCTION_ONLY", "cases": len(decisions)}) + "\n")
    (out / "runner.stderr.txt").write_text("")
    print(json.dumps({"status": "EXECUTED_HOST_CONSTRUCTION_ONLY", "raw_sha256": hashlib.sha256(payload.encode()).hexdigest(), "cases": len(decisions)}))


if __name__ == "__main__":
    main()
