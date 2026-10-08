import json
import pathlib
import sys


def classify(o):
    state, cert, rows = o["state"], o["certificate"], o["journal"]
    base = cert["base_revision"]
    rev = state["revision"]
    initial = cert["baseline_state"]
    if rev == base and not rows and state == initial:
        return {"decision": "NO_CHANGE", "proposal": None}
    if rev < base or len(rows) != rev - base:
        return {"decision": "UNKNOWN", "proposal": None}
    expected_revs = list(range(base + 1, rev + 1))
    if [r["revision"] for r in rows] != expected_revs or [r["seq"] for r in rows] != expected_revs:
        return {"decision": "UNKNOWN", "proposal": None}
    reconstructed = {k: initial[k] for k in ("agent_value", "external_value")}
    for row in rows:
        field = row["field"]
        if field not in reconstructed or reconstructed[field] != row["before_value"]:
            return {"decision": "UNKNOWN", "proposal": None}
        reconstructed[field] = row["after_value"]
    if reconstructed != {k: state[k] for k in reconstructed}:
        return {"decision": "UNKNOWN", "proposal": None}
    if any(r["field"] == cert["agent_field"] for r in rows):
        return {"decision": "UNKNOWN", "proposal": None}
    return {"decision": "PROPOSE_COMPENSATION", "proposal": {
        "restore_field": cert["agent_field"], "restore_value": cert["agent_original"],
        "preserve_field": "external_value", "preserve_value": state["external_value"],
        "bind_revision": rev}}


def main(observations_path, output_path):
    data = json.loads(pathlib.Path(observations_path).read_text())
    entries = data["observations"]
    ids = [o["case_id"] for o in entries]
    errors = []
    if len(ids) != len(set(ids)):
        errors.append("duplicate observation case_id")
    decisions = [{"case_id": o["case_id"], **classify(o)} for o in entries]
    result = {"allocation": data["allocation"], "decisions": decisions, "errors": errors}
    pathlib.Path(output_path).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"decisions": len(decisions), "errors": len(errors)}, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
