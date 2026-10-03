"""Raw-only independent conjunction oracle. Imports neither producer nor runtime."""
import argparse
import itertools
import json
from collections import Counter
from pathlib import Path

FIELDS = {"states", "bad_first", "duplicate", "release_tick", "verified", "backend",
          "first_bad", "duplicate_result", "first_preserved", "representation", "terminal",
          "final_stage", "command_id", "error", "calls"}


def audit(data):
    if type(data) is not dict or set(data) != {"schema", "revision", "environment", "rows"}:
        raise ValueError("top-level schema")
    if data["schema"] != "kernel-three-boundaries-v1" or data["revision"] not in {"baseline", "combined"}:
        raise ValueError("identity")
    env = data["environment"]
    if type(env) is not dict or set(env) != {"python", "platform", "machine"} or any(type(x) is not str or not x for x in env.values()):
        raise ValueError("environment")
    if type(data["rows"]) is not list:
        raise ValueError("rows type")
    expected = set(itertools.product(itertools.product(range(3), repeat=4), (False, True),
                                    ("none", "same", "different"), (499, 500, 800), (False, True)))
    seen = set()
    failures = Counter()
    faulty_rows = 0
    for row in data["rows"]:
        if type(row) is not dict or set(row) != FIELDS:
            raise ValueError("row schema")
        if type(row["states"]) is not list or len(row["states"]) != 4 or any(type(x) is not int for x in row["states"]):
            raise ValueError("states")
        if type(row["bad_first"]) is not bool or type(row["verified"]) is not bool or type(row["release_tick"]) is not int:
            raise ValueError("input types")
        if row["first_preserved"] is not None and type(row["first_preserved"]) is not bool:
            raise ValueError("preserved type")
        for name in ("backend", "first_bad", "duplicate_result", "representation", "terminal"):
            if type(row[name]) is not str or row[name] not in {"unreached", "accepted", "refused", "not_requested"}:
                raise ValueError("decision type")
        for name in ("final_stage", "command_id", "error"):
            if row[name] is not None and type(row[name]) is not str:
                raise ValueError("outcome type")
        calls = row["calls"]
        if type(calls) is not dict or set(calls) != {"probe", "observe", "execute", "release_all"} or any(type(x) is not int or x < 0 for x in calls.values()):
            raise ValueError("calls")
        key = (tuple(row["states"]), row["bad_first"], row["duplicate"], row["release_tick"], row["verified"])
        if key not in expected or key in seen:
            raise ValueError("coverage")
        seen.add(key)
        desired = dict(backend="refused", first_bad="unreached", duplicate_result="unreached",
                       first_preserved=None, representation="unreached", terminal="unreached",
                       final_stage=None, command_id=None, error=None,
                       calls=dict(probe=0, observe=0, execute=0, release_all=0))
        if all(x == 2 for x in row["states"]):
            current = row["release_tick"] >= 500
            terminal = current and row["verified"]
            desired.update(backend="accepted", first_bad="refused" if row["bad_first"] else "not_requested",
                           duplicate_result="not_requested" if row["duplicate"] == "none" else "refused",
                           first_preserved=True, representation="accepted" if current else "refused",
                           terminal=("accepted" if terminal else "refused") if current else "unreached",
                           final_stage="executed" if terminal else "authorized", command_id="first",
                           calls=dict(probe=1, observe=0, execute=0, release_all=0))
        diffs = [name for name in desired if row[name] != desired[name]]
        if diffs:
            faulty_rows += 1
            failures.update(diffs)
    if seen != expected:
        raise ValueError("missing rows")
    return dict(status="PASS_RAW_COVERAGE", revision=data["revision"], rows=len(seen),
                contract_mismatched_rows=faulty_rows, mismatches_by_field=dict(sorted(failures.items())))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("raw", type=Path)
    p.add_argument("output", type=Path)
    args = p.parse_args()
    result = audit(json.loads(args.raw.read_text()))
    with args.output.open("x") as f:
        json.dump(result, f, indent=2, sort_keys=True)
        f.write("\n")
    print(json.dumps(result, sort_keys=True))
    if result["revision"] == "combined" and result["contract_mismatched_rows"]:
        raise SystemExit(1)
