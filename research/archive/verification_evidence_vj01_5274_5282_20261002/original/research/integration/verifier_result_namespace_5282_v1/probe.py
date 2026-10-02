"""Finite identity-scope probe. No external I/O except explicit local evidence files."""
import hashlib
import itertools
import json
import os
from pathlib import Path
import sys
from reducer import Reducer
ROOT = Path(__file__).resolve().parent
PRODUCERS = {"alpha": "target", "beta": "effect", "gamma": "diagnostic", "delta": "target"}


def evaluate(events, scoped):
    r = Reducer()
    prefixes = r.view()
    for envelope in events:
        if not isinstance(envelope, dict):
            prefixes += r.feed(None)
            continue
        item = envelope.copy()
        producer = item.pop("producer", None)
        if type(producer) is not str or PRODUCERS.get(producer) != item.get("check") or producer not in PRODUCERS:
            prefixes += r.feed(None)
            continue
        if scoped and type(item.get("rid")) is str and 0 < len(item["rid"]) <= 48:
            item["rid"] = producer + ":" + item["rid"]
        elif type(item.get("rid")) is not str or not 0 < len(item["rid"]) <= 48:
            prefixes += r.feed(None)
            continue
        prefixes += r.feed(item)
    final = r.seal()
    late = r.feed(None) + r.seal()
    return {"prefix": prefixes, "final": final, "late": late, "authority": r.authority}


def main(output):
    freeze = json.loads((ROOT / "FREEZE.json").read_text())
    for name, record in freeze["files"].items():
        b = (ROOT / name).read_bytes()
        if len(b) != record["bytes"] or hashlib.sha256(b).hexdigest() != record["sha256"]:
            raise RuntimeError("SOURCE_MISMATCH:" + name)
    output.mkdir(parents=True, exist_ok=False)
    count = 0
    with (output / "raw.jsonl").open("x") as f:
        for case in json.loads((ROOT / "CASES.json").read_text()):
            for order in itertools.permutations(range(len(case["events"]))):
                events = [case["events"][i] for i in order]
                row = {"case": case["name"], "order": list(order), "events": events,
                       "bare": evaluate(events, False), "scoped": evaluate(events, True)}
                f.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
                count += 1
            f.flush()
        os.fsync(f.fileno())
    b = (output / "raw.jsonl").read_bytes()
    summary = {"allocation": freeze["allocation"], "rows": count, "bytes": len(b),
               "sha256": hashlib.sha256(b).hexdigest(), "formal_invocations": 1,
               "model_calls": 0, "gui_calls": 0, "retries": 0}
    (output / "SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
