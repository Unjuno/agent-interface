"""Independent oracle-side audit for the frozen multi-channel fixture."""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path


FIXTURE_SHA256 = "3114154c201a4d91f03607248fa5957ff2ba9f4be96b8c38f49840bbcbc3cd8d"
ORACLE_SHA256 = "f61d807d62e48745891edd7bedcb2f189e96b9346125272bda1d864034be7bd9"
CHANNELS = ("runtime", "watcher", "verifier", "post_effect_audit")
FAULT_CLASSES = {
    "stale_observation", "wrong_target", "partial_external_effect",
    "lost_critical_event", "delayed_ack_uncertain_delivery",
    "unreleased_held_input",
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reconstruct_expected(fixture):
    rows = []
    for channel, cfg in fixture["channels"].items():
        detected, unknown = set(cfg["detected"]), set(cfg["unknown"])
        for opportunity in fixture["opportunities"]:
            oid = opportunity["id"]
            is_detected, is_unknown = oid in detected, oid in unknown
            status = "detected" if is_detected else ("unknown" if is_unknown else "not_detected")
            delay = cfg["latency_ms"] if is_detected else None
            rows.append({
                "opportunity_id": oid, "channel": channel,
                "source_id": cfg["source_id"], "source_group": cfg["source_group"],
                "t0_ms": opportunity["t0_ms"], "status": status,
                "timestamp_ms": opportunity["t0_ms"] + delay if is_detected else None,
                "detection_delay_ms": delay,
                "link_key": fixture["linkage_key_prefix"] + oid,
                "alerted_by": fixture["alerted_by"].get(channel, {}).get(oid, []),
                "unknown_reason": fixture["unknown_reason"] if is_unknown else None,
            })
    return rows


def audit(data, fixture, oracle, *, fixture_path, oracle_path):
    require(sha256(fixture_path) == FIXTURE_SHA256, "frozen fixture hash mismatch")
    require(sha256(oracle_path) == ORACLE_SHA256, "frozen oracle hash mismatch")
    require(data["format"] == "oracle-ascertainment-candidate-a01-v1", "candidate format mismatch")
    require(data["main_sha"] == "708ca59a8128f07fdb7e13a36704c6b2f79c9fb6", "main identity mismatch")
    require(data["fixture_sha256"] == FIXTURE_SHA256 and data["oracle_loaded"] is False,
            "candidate fixture/oracle boundary mismatch")
    ids = [item["id"] for item in fixture["opportunities"]]
    require(len(ids) == 18 and len(set(ids)) == 18, "opportunity frame is not 18 unique IDs")
    require(tuple(fixture["channels"]) == CHANNELS, "channel set/order mismatch")
    expected = reconstruct_expected(fixture)
    observed = data["records"]
    require(len(observed) == 72, "incomplete or duplicated channel/opportunity rows")
    keys = [(r["opportunity_id"], r["channel"]) for r in observed]
    require(len(set(keys)) == 72, "duplicate channel/opportunity linkage")
    require(observed == expected, "candidate rows differ from independently reconstructed fixture")

    truth_rows = oracle["opportunities"]
    truth_ids = [r["id"] for r in truth_rows]
    require(len(truth_ids) == 18 and set(truth_ids) == set(ids) and len(set(truth_ids)) == 18,
            "oracle frame/linkage mismatch")
    truth = {r["id"]: r for r in truth_rows}
    faults = [r for r in truth_rows if r["has_fault"] is True]
    controls = [r for r in truth_rows if r["has_fault"] is False]
    require(len(faults) == 12 and len(controls) == 6, "oracle fault/control denominator mismatch")
    class_counts = Counter(r["fault_class"] for r in faults)
    require(set(class_counts) == FAULT_CLASSES and all(n == 2 for n in class_counts.values()),
            "six fault classes must each contain two opportunities")

    detections = {c: {r["opportunity_id"] for r in observed
                      if r["channel"] == c and r["status"] == "detected"}
                  for c in CHANNELS}
    fault_ids = {r["id"] for r in faults}
    channel_tp = {c: detections[c] & fault_ids for c in CHANNELS}
    union = set.union(*channel_tp.values())
    missed_all = fault_ids - union
    exclusive = {oid: [c for c in CHANNELS if oid in channel_tp[c]]
                 for oid in fault_ids if oid in union}
    channel_false = {c: detections[c] - fault_ids for c in CHANNELS}
    require(len(union) == 9 and missed_all == {"F02", "F04", "F08"},
            "oracle ascertainment coverage/common blind-spot mismatch")
    require(any(len(channels) == 1 for channels in exclusive.values()),
            "fixture lacks channel-exclusive detection")
    require(channel_false == {"runtime": {"N16"}, "watcher": set(),
                              "verifier": set(), "post_effect_audit": set()},
            "false-report vector mismatch")
    unknown_rows = [r for r in observed if r["status"] == "unknown"]
    require([(r["opportunity_id"], r["channel"]) for r in unknown_rows] == [("N18", "verifier")],
            "UNKNOWN must remain distinct from no-fault/non-detection")
    require(sum(len(r.get("alerted_by", [])) for r in observed) == 3,
            "known channel-alert dependency edges mismatch")

    runtime_reports, watcher_reports = detections["runtime"], detections["watcher"]
    n1, n2, overlap = len(runtime_reports), len(watcher_reports), len(runtime_reports & watcher_reports)
    naive = n1 * n2 / overlap
    chapman = ((n1 + 1) * (n2 + 1) / (overlap + 1)) - 1
    require((n1, n2, overlap) == (5, 3, 2), "two-list counts mismatch")
    require(data["runtime_watcher_diagnostic"]["naive_two_list_estimate"] == naive and
            data["runtime_watcher_diagnostic"]["chapman_estimate"] == chapman,
            "candidate estimator arithmetic mismatch")
    require(naive < len(faults) and chapman < len(faults), "diagnostic did not undercount fixture faults")
    return {
        "opportunities": len(ids), "faults": len(faults), "controls": len(controls),
        "union_detected_faults": len(union), "union_recall": len(union) / len(faults),
        "missed_by_all": sorted(missed_all), "channel_true_positives": {k: len(v) for k, v in channel_tp.items()},
        "false_reports": {k: sorted(v) for k, v in channel_false.items()},
        "unknown_cells": [(r["opportunity_id"], r["channel"]) for r in unknown_rows],
        "runtime_watcher": {"n1": n1, "n2": n2, "overlap": overlap,
                            "naive_estimate": naive, "chapman_estimate": chapman,
                            "oracle_fault_total": len(faults),
                            "naive_underestimate_fraction": (len(faults) - naive) / len(faults)},
    }


def main(candidate_path):
    root = Path(__file__).resolve().parent
    fixture_path, oracle_path = root / "fixture.json", root / "ORACLE.json"
    data = json.loads(Path(candidate_path).read_text(encoding="utf-8"))
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    oracle = json.loads(oracle_path.read_text(encoding="utf-8"))
    result = audit(data, fixture, oracle, fixture_path=fixture_path, oracle_path=oracle_path)
    print("PASS_METHOD_SCOPED_HOST")
    print(json.dumps(result, sort_keys=True))
    print("container transfer gate: HOLD_CONTAINER_TRANSFER (not exercised)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: audit_result.py candidate.json")
    try:
        main(sys.argv[1])
    except Exception as error:
        print(f"FAIL: {type(error).__name__}: {error}")
        raise SystemExit(1)
