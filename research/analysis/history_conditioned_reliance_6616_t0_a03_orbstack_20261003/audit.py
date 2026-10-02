"""Independent raw-only audit for Issue #6616 T0 stimulus construction."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys


ALLOCATION = "history-conditioned-reliance-6616-t0-a03-20261003"
IMAGE = "sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f"
OPTIONS = ["accept_result", "inspect_evidence", "reconcile_before_retry", "safe_takeover"]
ERRORS = ("false_success", "unknown_partial", "dispatch_only", "dispatch_only")


class AuditError(Exception):
    pass


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def require(condition: bool, code: str) -> None:
    if not condition:
        raise AuditError(code)


def verify_environment(freeze: dict, freeze_bytes: bytes, candidate: dict) -> None:
    env = {k: os.environ.get(k) for k in ("OBSTAC_ALLOCATION_ID", "OBSTAC_SOURCE_COMMIT", "OBSTAC_IMAGE_ID",
                                           "OBSTAC_FREEZE_SHA256", "OBSTAC_CONSTRUCTION")}
    expected = {"OBSTAC_ALLOCATION_ID": ALLOCATION, "OBSTAC_SOURCE_COMMIT": freeze["source_commit"],
                "OBSTAC_IMAGE_ID": IMAGE, "OBSTAC_FREEZE_SHA256": sha(freeze_bytes), "OBSTAC_CONSTRUCTION": "0"}
    require(env == expected, "obstac_environment_mismatch")
    require(candidate.get("execution_receipt", {}).get("OBSTAC_FREEZE_SHA256") == sha(freeze_bytes),
            "candidate_freeze_receipt_mismatch")
    require(candidate.get("execution_receipt", {}).get("OBSTAC_SOURCE_COMMIT") == freeze["source_commit"],
            "candidate_source_receipt_mismatch")
    require(candidate.get("execution_receipt", {}).get("OBSTAC_IMAGE_ID") == IMAGE, "candidate_image_receipt_mismatch")


def hidden_keys(value: object) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            if any(token in key.lower() for token in ("oracle", "correct_action", "latent_effect", "true_effect")):
                return True
            if hidden_keys(child):
                return True
    elif isinstance(value, list):
        return any(hidden_keys(x) for x in value)
    return False


def expected_rows(fixture: dict) -> list[dict]:
    counts = fixture["expected_history_counts"]
    require(sum(counts.values()) == fixture["sequence_length"], "history_count_total")
    sequences = fixture["sequences"]
    require(len(sequences) == 4 and len({x["sequence_id"] for x in sequences}) == 4, "sequence_coverage")
    canonical_orders = []
    for sequence in sequences:
        order = sequence["order"]
        got = {kind: order.count(kind) for kind in counts}
        require(len(order) == fixture["sequence_length"] and got == counts, "equal_history_multiset")
        canonical_orders.append(tuple(order))
    require(len(set(canonical_orders)) == 4, "order_manipulations_distinct")
    probes, arms = fixture["probes"], fixture["presentation_arms"]
    require(len(probes) == 3 and len(arms) == 3, "factorial_cells")
    expected = []
    for sequence in sequences:
        event_rows = []
        for position, kind in enumerate(sequence["order"], 1):
            event = {"receipt_id": f"{sequence['sequence_id']}-event-{position:02d}",
                     **fixture["history_event_display"][kind]}
            event["source_digest"] = sha(canonical(event))
            event_rows.append(event)
        for probe in probes:
            for arm in arms:
                row = {"row_id": f"{sequence['sequence_id']}|{probe['probe_id']}|{arm['arm_id']}",
                       "sequence_id": sequence["sequence_id"], "probe_id": probe["probe_id"],
                       "arm_id": arm["arm_id"], "current_receipt": probe["current_receipt"],
                       "raw_evidence": probe["raw_evidence"],
                       "task_metadata": {k: v for k, v in fixture["task_metadata"].items() if k != "action_options"},
                       "action_options": OPTIONS,
                       "visible_history": event_rows if arm["show_ordered_history"] else [],
                       "reminder": arm["reminder"]}
                row["row_sha256"] = sha(canonical(row))
                expected.append(row)
    return expected


def validate_design_roles(fixture: dict, oracle: dict) -> None:
    require(oracle.get("schema") == "history-conditioned-reliance-hidden-oracle-v1" and
            oracle.get("allocation_id") == ALLOCATION, "oracle_identity")
    roles = oracle.get("condition_role", {})
    require(roles == {"h-01": "early_error", "h-02": "late_error", "h-03": "clustered_error",
                      "h-04": "evenly_spaced_error_control"}, "condition_role_roster")
    expected_orders = {
        "early_error": ["false_success", "unknown_partial", "dispatch_only", "dispatch_only",
                         "verified_success", "verified_success", "verified_success", "verified_success"],
        "late_error": ["verified_success", "verified_success", "verified_success", "verified_success",
                        "false_success", "unknown_partial", "dispatch_only", "dispatch_only"],
        "clustered_error": ["verified_success", "verified_success", "false_success", "unknown_partial",
                            "dispatch_only", "dispatch_only", "verified_success", "verified_success"],
        "evenly_spaced_error_control": ["verified_success", "false_success", "verified_success", "dispatch_only",
                                        "verified_success", "unknown_partial", "verified_success", "dispatch_only"],
    }
    by_id = {s["sequence_id"]: s["order"] for s in fixture["sequences"]}
    require(set(by_id) == set(roles), "sequence_role_coverage")
    require(all(by_id[sequence_id] == expected_orders[role] for sequence_id, role in roles.items()),
            "sequence_role_pattern")
    metadata = fixture["task_metadata"]
    require(metadata.get("action_options") == OPTIONS, "common_action_options")
    require(set(metadata) == {"task_family", "difficulty_band", "layout_id", "action_options"},
            "task_metadata_fields")
    required_status = {"p-verified": "verified_success", "p-dispatch": "dispatch_only", "p-unknown": "unknown_partial"}
    require({p["probe_id"]: p["current_receipt"].get("typed_status") for p in fixture["probes"]} == required_status,
            "probe_status_roster")
    for probe in fixture["probes"]:
        raw = probe["raw_evidence"]
        require(raw.get("task_family") == metadata["task_family"] and
                raw.get("difficulty_band") == metadata["difficulty_band"] and
                raw.get("layout_id") == metadata["layout_id"], "probe_task_metadata_match")


def validate_packets(rows: list[dict], packets: dict) -> None:
    require(set(packets) == {"schema", "packets"} and packets["schema"] ==
            "history-conditioned-reliance-review-packets-v1", "review_packet_schema")
    require([p["packet_id"] for p in packets["packets"]] == ["blind-packet-a", "blind-packet-b"],
            "review_packet_pair")
    allowed = {"current_receipt", "raw_evidence", "task_metadata", "action_options", "visible_history", "reminder", "arm_id"}
    expected_displays = []
    for row in rows:
        display = {k: row[k] for k in allowed}
        expected_displays.append(canonical(display))
    for packet in packets["packets"]:
        require(set(packet) == {"packet_id", "items"} and len(packet["items"]) == len(rows), "review_packet_count")
        identities = set()
        actual_displays = []
        for item in packet["items"]:
            require(set(item) == {"opaque_item_id", "stimulus"}, "review_item_schema")
            require(not hidden_keys(item), "oracle_leak_to_reviewer")
            require(item["opaque_item_id"] not in identities, "review_item_id_duplicate")
            identities.add(item["opaque_item_id"])
            require(set(item["stimulus"]) == allowed, "review_stimulus_fields")
            require(item["stimulus"]["action_options"] == OPTIONS, "review_action_options")
            actual_displays.append(canonical(item["stimulus"]))
        require(sorted(actual_displays) == sorted(expected_displays), "review_packet_content_mismatch")


def validate(fixture: dict, oracle: dict, candidate: dict, packets: dict, receipt_env: dict | None = None) -> dict:
    require(set(candidate) == {"schema", "allocation_id", "execution_receipt", "row_count", "rows"},
            "candidate_root_fields")
    require(candidate["schema"] == "history-conditioned-reliance-candidate-raw-v1" and
            candidate["allocation_id"] == ALLOCATION, "candidate_identity")
    require(not hidden_keys(candidate), "oracle_leak_to_candidate")
    validate_design_roles(fixture, oracle)
    expected = expected_rows(fixture)
    require(candidate["row_count"] == 36 and len(candidate["rows"]) == 36, "row_denominator")
    require(candidate["rows"] == expected, "raw_rows_not_reconstructed")
    validate_packets(expected, packets)
    oracle_map = oracle["probe_truth"]
    require(set(oracle_map) == {p["probe_id"] for p in fixture["probes"]}, "oracle_probe_coverage")
    for probe in fixture["probes"]:
        truth = oracle_map[probe["probe_id"]]
        require(truth["correct_action"] in OPTIONS, "oracle_action_outside_options")
        if probe["probe_id"] == "p-verified":
            require(probe["current_receipt"]["typed_status"] == "verified_success" and
                    truth["independent_effect"] == "present_exact" and truth["correct_action"] == "accept_result",
                    "verified_success_oracle")
        elif probe["probe_id"] == "p-dispatch":
            require(probe["current_receipt"]["typed_status"] == "dispatch_only" and
                    truth["independent_effect"] == "absent" and truth["correct_action"] == "reconcile_before_retry",
                    "dispatch_only_oracle")
        elif probe["probe_id"] == "p-unknown":
            require(probe["current_receipt"]["typed_status"] == "unknown_partial" and
                    truth["independent_effect"] == "present_but_current_evidence_insufficient" and
                    truth["correct_action"] == "safe_takeover", "unknown_partial_oracle")
    return {"rows_reconstructed": len(expected), "unique_rows": len({r["row_id"] for r in expected}),
            "history_multiset_equal": True, "current_probe_crossed_with_every_sequence_and_arm": True,
            "oracle_separated_from_candidate_and_review_packets": True, "human_responses": 0,
            "independent_human_reviewers": 0, "reviewer_signoff": "NOT_COLLECTED"}


def corruption_controls(fixture: dict, oracle: dict, candidate: dict, packets: dict) -> dict:
    outcomes = {}
    cases = {}
    raw = json.loads(json.dumps(candidate))
    a = next(i for i, r in enumerate(raw["rows"]) if r["row_id"] == "h-01|p-verified|current-only")
    b = next(i for i, r in enumerate(raw["rows"]) if r["row_id"] == "h-01|p-dispatch|current-only")
    raw["rows"][a]["raw_evidence"], raw["rows"][b]["raw_evidence"] = raw["rows"][b]["raw_evidence"], raw["rows"][a]["raw_evidence"]
    cases["swap_current_raw_evidence"] = (fixture, oracle, raw, packets)
    raw = json.loads(json.dumps(candidate))
    raw["rows"][next(i for i, r in enumerate(raw["rows"]) if r["row_id"] ==
                       "h-01|p-unknown|current-only")]["current_receipt"]["typed_status"] = "verified_success"
    cases["relabel_unknown_as_success"] = (fixture, oracle, raw, packets)
    mutated = json.loads(json.dumps(fixture))
    mutated["sequences"][0]["order"][0] = "verified_success"
    cases["alter_total_history_type_counts"] = (mutated, oracle, candidate, packets)
    raw = json.loads(json.dumps(candidate))
    raw["rows"][0]["correct_action"] = "accept_result"
    cases["leak_final_oracle_to_candidate"] = (fixture, oracle, raw, packets)
    for name, values in cases.items():
        try:
            validate(*values)
        except (AuditError, KeyError, TypeError, ValueError):
            outcomes[name] = "REJECTED"
        else:
            outcomes[name] = "ACCEPTED_UNEXPECTEDLY"
    require(all(v == "REJECTED" for v in outcomes.values()), "corruption_control_failed")
    return outcomes


def run(fixture_path: Path, oracle_path: Path, freeze_path: Path, candidate_path: Path,
        packets_path: Path, out_path: Path) -> None:
    freeze_bytes = freeze_path.read_bytes()
    freeze = json.loads(freeze_bytes)
    for name in ("audit.py", "fixture.json", "oracle.json", "candidate.py"):
        require(sha((Path("/src") / name).read_bytes()) == freeze["source_sha256"][name], "frozen_source_hash_" + name)
    fixture, oracle = json.loads(fixture_path.read_text()), json.loads(oracle_path.read_text())
    candidate, packets = json.loads(candidate_path.read_text()), json.loads(packets_path.read_text())
    verify_environment(freeze, freeze_bytes, candidate)
    gates = validate(fixture, oracle, candidate, packets)
    mutations = corruption_controls(fixture, oracle, candidate, packets)
    report = {"schema": "history-conditioned-reliance-independent-audit-v1", "allocation_id": ALLOCATION,
              "candidate_exit_claim": "not inferred from raw; launcher receipt required",
              "disposition": "PASS_CONSTRUCTION_MECHANICS_HOLD_INDEPENDENT_REVIEWER_SIGNOFF",
              "gates": gates, "corruption_controls": mutations,
              "scoring_key": oracle["probe_truth"], "condition_roles": oracle["condition_role"],
              "scope": "No participants or human responses; stimulus/scorer construction only. Reviewer packets are prepared but unsigned."}
    out_path.parent.mkdir(parents=True, exist_ok=False)
    out_path.write_bytes(canonical(report) + b"\n")


if __name__ == "__main__":
    if len(sys.argv) != 7:
        raise SystemExit("usage: audit.py FIXTURE ORACLE FREEZE CANDIDATE_RAW REVIEWER_PACKETS OUTPUT")
    run(*(Path(x) for x in sys.argv[1:]))
