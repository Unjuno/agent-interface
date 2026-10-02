"""Build candidate-visible Issue #6616 T0 stimulus rows without hidden truth."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys

ALLOCATION = "history-conditioned-reliance-6616-t0-a03-20261003"
IMAGE = "sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f"
OUTCOMES = {"verified_success", "dispatch_only", "unknown_partial", "false_success"}
OPTIONS = ["accept_result", "inspect_evidence", "reconcile_before_retry", "safe_takeover"]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def validate_fixture(fixture: dict) -> None:
    required = {"schema", "allocation_id", "sequence_length", "expected_history_counts", "sequences",
                "history_event_display", "task_metadata", "probes", "presentation_arms"}
    if set(fixture) != required or fixture["schema"] != "history-conditioned-reliance-stimulus-v1":
        raise ValueError("fixture_schema_or_fields")
    if fixture["allocation_id"] != ALLOCATION or fixture["sequence_length"] != 8:
        raise ValueError("fixture_allocation_or_length")
    counts = fixture["expected_history_counts"]
    if set(counts) != OUTCOMES or sum(counts.values()) != fixture["sequence_length"]:
        raise ValueError("history_count_schema")
    seqs = fixture["sequences"]
    if len(seqs) != 4 or len({s["sequence_id"] for s in seqs}) != 4:
        raise ValueError("sequence_coverage")
    for seq in seqs:
        if set(seq) != {"sequence_id", "order"} or len(seq["order"]) != fixture["sequence_length"]:
            raise ValueError("sequence_shape")
        if set(seq["order"]) != OUTCOMES or {x: seq["order"].count(x) for x in OUTCOMES} != counts:
            raise ValueError("sequence_multiset")
    if len({tuple(s["order"]) for s in seqs}) != 4:
        raise ValueError("sequence_order_not_distinct")
    probes = fixture["probes"]
    if len(probes) != 3 or len({p["probe_id"] for p in probes}) != 3:
        raise ValueError("probe_coverage")
    if fixture["task_metadata"].get("action_options") != OPTIONS:
        raise ValueError("action_options_mismatch")
    if len(fixture["presentation_arms"]) != 3:
        raise ValueError("presentation_arm_coverage")
    for probe in probes:
        if set(probe) != {"probe_id", "current_receipt", "raw_evidence"}:
            raise ValueError("probe_schema")
        for key in ("task_family", "difficulty_band", "layout_id"):
            if probe["raw_evidence"].get(key) != fixture["task_metadata"][key]:
                raise ValueError("probe_task_metadata_mismatch")


def build_rows(fixture: dict) -> list[dict]:
    validate_fixture(fixture)
    rows = []
    for sequence in fixture["sequences"]:
        history = []
        for index, outcome in enumerate(sequence["order"], 1):
            event = {"receipt_id": f"{sequence['sequence_id']}-event-{index:02d}",
                     **fixture["history_event_display"][outcome]}
            event["source_digest"] = sha(canonical(event))
            history.append(event)
        for probe in fixture["probes"]:
            for arm in fixture["presentation_arms"]:
                body = {
                    "row_id": f"{sequence['sequence_id']}|{probe['probe_id']}|{arm['arm_id']}",
                    "sequence_id": sequence["sequence_id"], "probe_id": probe["probe_id"],
                    "arm_id": arm["arm_id"], "current_receipt": probe["current_receipt"],
                    "raw_evidence": probe["raw_evidence"],
                    "task_metadata": {k: v for k, v in fixture["task_metadata"].items() if k != "action_options"},
                    "action_options": OPTIONS,
                    "visible_history": history if arm["show_ordered_history"] else [],
                    "reminder": arm["reminder"],
                }
                body["row_sha256"] = sha(canonical(body))
                rows.append(body)
    return rows


def make_packets(rows: list[dict]) -> dict:
    packets = []
    fields = ("current_receipt", "raw_evidence", "task_metadata", "action_options", "visible_history", "reminder", "arm_id")
    for packet_id in ("blind-packet-a", "blind-packet-b"):
        keyed = []
        for row in rows:
            display = {k: row[k] for k in fields}
            token = sha((packet_id + "|" + row["row_id"]).encode("utf-8"))[:16]
            keyed.append((token, display))
        keyed.sort(key=lambda x: x[0], reverse=packet_id.endswith("b"))
        packets.append({"packet_id": packet_id,
                        "items": [{"opaque_item_id": token, "stimulus": display} for token, display in keyed]})
    return {"schema": "history-conditioned-reliance-review-packets-v1", "packets": packets}


def run(fixture_path: Path, freeze_path: Path, out_dir: Path) -> None:
    freeze_bytes = freeze_path.read_bytes()
    freeze = json.loads(freeze_bytes)
    env = {k: os.environ.get(k) for k in ("OBSTAC_ALLOCATION_ID", "OBSTAC_SOURCE_COMMIT", "OBSTAC_IMAGE_ID",
                                           "OBSTAC_FREEZE_SHA256", "OBSTAC_CONSTRUCTION")}
    expected = {"OBSTAC_ALLOCATION_ID": ALLOCATION, "OBSTAC_SOURCE_COMMIT": freeze["base_main_sha"],
                "OBSTAC_IMAGE_ID": IMAGE, "OBSTAC_FREEZE_SHA256": sha(freeze_bytes), "OBSTAC_CONSTRUCTION": "0"}
    if env != expected or sha(Path(__file__).read_bytes()) != freeze["source_sha256"]["candidate.py"]:
        raise SystemExit("STOP_OBSTAC_OR_SOURCE_PROVENANCE_MISMATCH")
    fixture_bytes = fixture_path.read_bytes()
    if sha(fixture_bytes) != freeze["source_sha256"]["fixture.json"]:
        raise SystemExit("STOP_FIXTURE_HASH_MISMATCH")
    fixture = json.loads(fixture_bytes)
    rows = build_rows(fixture)
    raw = {"schema": "history-conditioned-reliance-candidate-raw-v1", "allocation_id": ALLOCATION,
           "execution_receipt": {**env, "candidate_sha256": sha(Path(__file__).read_bytes()),
                                 "fixture_sha256": sha(fixture_bytes)}, "row_count": len(rows), "rows": rows}
    out_dir.mkdir(parents=True, exist_ok=False)
    (out_dir / "candidate.raw.json").write_bytes(canonical(raw) + b"\n")
    (out_dir / "reviewer_packets.json").write_bytes(canonical(make_packets(rows)) + b"\n")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: candidate.py FIXTURE FREEZE OUTPUT_DIR")
    run(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
