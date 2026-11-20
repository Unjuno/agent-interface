"""Independent raw-only audit; repeats selection and predicate without candidate imports."""
import argparse
import hashlib
import json
import zipfile

EXPECTED_ARCHIVE_SHA256 = "b6e8529a51e89e6f1c51374fbd27f121bab594c92014ee2fe73aa2f94ef98163"
SELECTED = (0, 1, 2, 3, 5)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("archive")
    args = ap.parse_args()
    with open(args.archive, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    if digest != EXPECTED_ARCHIVE_SHA256:
        raise SystemExit(f"STOP_INPUT_HASH:{digest}")
    with zipfile.ZipFile(args.archive) as zf:
        decisions = json.loads(zf.read("report.json"))["decisions"]
        raw = [json.loads(line) for line in zf.read("runtime/events.jsonl").decode().splitlines()]
    observations = [e for e in raw if e.get("event") == "typed_observation"]
    output = []
    for d in decisions:
        i = d["iteration"]
        if i not in SELECTED:
            continue
        right = d["planner_terminal_observed_ns"]
        left = right - d["model_ns"]
        history = [e for e in observations if e.get("emit_ns", 0) <= left and
                   e.get("signals", {}).get("health", {}).get("status") == "observed"]
        if len(history) == 0:
            raise SystemExit(f"STOP_BASELINE:{i}")
        baseline_row = history[-1]
        baseline = baseline_row["signals"]["health"]["value"]
        stream_names = {"cover-%s" % i, "cover-%s-renew-1" % i}
        samples = []
        for e in observations:
            health = e.get("signals", {}).get("health", {})
            stamp = e.get("emit_ns", -1)
            if e.get("id") in stream_names and left <= stamp <= right and health.get("status") == "observed":
                samples.append({"sequence": e["sequence"], "emit_ns": stamp,
                                "health": health["value"]})
        last_three = []
        hit = None
        for sample in samples:
            last_three = (last_three + [sample["health"] <= baseline - 5])[-3:]
            if sum(last_three) >= 2:
                hit = {"sequence": sample["sequence"], "emit_ns": sample["emit_ns"],
                       "health": sample["health"]}
                break
        output.append({"decision": i, "window_start_ns": left, "window_end_ns": right,
                       "baseline_sequence": baseline_row["sequence"],
                       "baseline_health": baseline, "eligible_samples": len(samples), "trigger": hit})
    print(json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()

