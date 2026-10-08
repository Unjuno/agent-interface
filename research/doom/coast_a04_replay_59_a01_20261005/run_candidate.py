"""Candidate-side raw archive replay. This is post-hoc descriptive only."""
import argparse
import hashlib
import json
import zipfile

from CANDIDATE import candidate

EXPECTED_ARCHIVE_SHA256 = "b6e8529a51e89e6f1c51374fbd27f121bab594c92014ee2fe73aa2f94ef98163"
SELECTED = (0, 1, 2, 3, 5)


def load(archive):
    digest = hashlib.sha256(open(archive, "rb").read()).hexdigest()
    if digest != EXPECTED_ARCHIVE_SHA256:
        raise SystemExit(f"STOP_INPUT_HASH:{digest}")
    with zipfile.ZipFile(archive) as zf:
        report = json.loads(zf.read("report.json"))
        events = [json.loads(line) for line in zf.read("runtime/events.jsonl").decode().splitlines()]
    return report, [e for e in events if e.get("event") == "typed_observation"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("archive")
    args = ap.parse_args()
    report, events = load(args.archive)
    output = []
    for decision in report["decisions"]:
        i = decision["iteration"]
        if i not in SELECTED:
            continue
        end = decision["planner_terminal_observed_ns"]
        start = end - decision["model_ns"]
        prior = [e for e in events if e.get("emit_ns", 0) <= start and
                 e.get("signals", {}).get("health", {}).get("status") == "observed"]
        if not prior:
            raise SystemExit(f"STOP_BASELINE:{i}")
        baseline_row = prior[-1]
        stream_ids = (f"cover-{i}", f"cover-{i}-renew-1")
        rows = []
        for e in events:
            h = e.get("signals", {}).get("health", {})
            if (e.get("id") in stream_ids and start <= e.get("emit_ns", 0) <= end
                    and h.get("status") == "observed"):
                rows.append({"sequence": e["sequence"], "emit_ns": e["emit_ns"],
                             "health": h["value"]})
        trigger = candidate(baseline_row["signals"]["health"]["value"], rows)
        output.append({"decision": i, "window_start_ns": start, "window_end_ns": end,
                       "baseline_sequence": baseline_row["sequence"],
                       "baseline_health": baseline_row["signals"]["health"]["value"],
                       "eligible_samples": len(rows), "trigger": trigger})
    print(json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()

