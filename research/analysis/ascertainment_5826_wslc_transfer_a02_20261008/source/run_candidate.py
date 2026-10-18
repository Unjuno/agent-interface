"""Deterministically materialize the frozen channel observations (oracle-blind)."""
import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path

FIXTURE_SHA256 = "3114154c201a4d91f03607248fa5957ff2ba9f4be96b8c38f49840bbcbc3cd8d"
MAIN_SHA = "708ca59a8128f07fdb7e13a36704c6b2f79c9fb6"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    fixture_path = root / "fixture.json"
    if sha256(fixture_path) != FIXTURE_SHA256:
        raise SystemExit("fixture identity mismatch; candidate not run")
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    opportunities = fixture["opportunities"]
    rows = []
    captures = {}
    for channel, config in fixture["channels"].items():
        detected = set(config["detected"])
        unknown = set(config["unknown"])
        captures[channel] = detected
        for opportunity in opportunities:
            oid = opportunity["id"]
            is_detected = oid in detected
            is_unknown = oid in unknown
            status = "detected" if is_detected else ("unknown" if is_unknown else "not_detected")
            delay = config["latency_ms"] if is_detected else None
            rows.append({
                "opportunity_id": oid,
                "channel": channel,
                "source_id": config["source_id"],
                "source_group": config["source_group"],
                "t0_ms": opportunity["t0_ms"],
                "status": status,
                "timestamp_ms": opportunity["t0_ms"] + delay if is_detected else None,
                "detection_delay_ms": delay,
                "link_key": fixture["linkage_key_prefix"] + oid,
                "alerted_by": fixture["alerted_by"].get(channel, {}).get(oid, []),
                "unknown_reason": fixture["unknown_reason"] if is_unknown else None,
            })
    runtime, watcher = captures["runtime"], captures["watcher"]
    overlap = runtime & watcher
    n1, n2, m = len(runtime), len(watcher), len(overlap)
    result = {
        "format": "oracle-ascertainment-candidate-a01-v1",
        "main_sha": MAIN_SHA,
        "fixture_sha256": FIXTURE_SHA256,
        "oracle_loaded": False,
        "environment": {"python": sys.version.split()[0],
                        "platform": platform.platform(),
                        "machine": platform.machine()},
        "records": rows,
        "runtime_watcher_diagnostic": {
            "list_1": "runtime", "list_2": "watcher",
            "n1_reports": n1, "n2_reports": n2, "overlap_reports": m,
            "naive_two_list_estimate": (n1 * n2 / m) if m else None,
            "chapman_estimate": (((n1 + 1) * (n2 + 1) / (m + 1)) - 1) if m else None,
            "interpretation": "oracle-blind diagnostic only; not a production unseen-fault estimate",
        },
    }
    target = Path(args.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(f"candidate opportunities={len(opportunities)} channel_rows={len(rows)} output={target} (exclusive create)")


if __name__ == "__main__":
    main()
