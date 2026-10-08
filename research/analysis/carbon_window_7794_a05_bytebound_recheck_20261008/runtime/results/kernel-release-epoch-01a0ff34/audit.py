"""Independent raw-only schema/coverage/order audit; imports no runtime or producer."""
import argparse
import json
from pathlib import Path
import re

ROW_FIELDS = {"started_ns", "ended_ns", "observed_ns", "verified",
              "representation_accepted", "terminal_accepted"}


def audit(data):
    if type(data) is not dict or set(data) != {"schema", "revision", "source_sha256", "environment", "rows"}:
        raise ValueError("matrix schema")
    if data["schema"] != "kernel-release-epoch-matrix-v1" or data["revision"] not in ("baseline", "fixed"):
        raise ValueError("matrix identity")
    if type(data["source_sha256"]) is not str or not re.fullmatch("[0-9a-f]{64}", data["source_sha256"]):
        raise ValueError("source hash")
    env = data["environment"]
    if type(env) is not dict or set(env) != {"python", "platform"} or any(type(x) is not str or not x for x in env.values()):
        raise ValueError("environment")
    if type(data["rows"]) is not list:
        raise ValueError("rows type")
    expected = {(s, e, r, v) for s in range(5) for e in range(s, 5) for r in range(7) for v in (False, True)}
    seen = set()
    representation_gaps = terminal_gaps = 0
    for row in data["rows"]:
        if type(row) is not dict or set(row) != ROW_FIELDS:
            raise ValueError("row schema")
        if any(type(row[k]) is not int for k in ("started_ns", "ended_ns", "observed_ns")):
            raise ValueError("timestamp type")
        if any(type(row[k]) is not bool for k in ("verified", "representation_accepted", "terminal_accepted")):
            raise ValueError("decision type")
        key = tuple(row[k] for k in ("started_ns", "ended_ns", "observed_ns", "verified"))
        if key not in expected or key in seen:
            raise ValueError("row coverage")
        seen.add(key)
        # Reference order: put release before execution only when its tick is lower.
        order = sorted(((row["started_ns"], 0, "start"), (row["observed_ns"], 1, "release")))
        current = order[0][2] == "start"
        wanted = True if data["revision"] == "baseline" else current
        if row["representation_accepted"] != wanted:
            raise ValueError("representation reconstruction")
        if row["terminal_accepted"] != (wanted and row["verified"]):
            raise ValueError("terminal reconstruction")
        representation_gaps += row["representation_accepted"] and not current
        terminal_gaps += row["terminal_accepted"] and not current
    if seen != expected:
        raise ValueError("incomplete coverage")
    return dict(status="PASS_RAW_RECONSTRUCTION", rows=len(seen),
                prestart_representation_gaps=representation_gaps,
                prestart_terminal_gaps=terminal_gaps, revision=data["revision"],
                source_sha256=data["source_sha256"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("raw", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = audit(json.loads(args.raw.read_text(encoding="utf-8")))
    with args.output.open("x", encoding="utf-8", newline="\n") as out:
        json.dump(result, out, indent=2, sort_keys=True)
        out.write("\n")
    print(json.dumps(result, sort_keys=True))
