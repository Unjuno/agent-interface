"""Independent join audit for the retained V39 fake-X startup trace."""
from __future__ import annotations

import copy
import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PKG = ROOT / "research/doom/v39_startup_edge_identity_audit_a01_20261005"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def verify_freeze(freeze):
    errors = []
    head = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True).stdout.strip()
    ancestry = subprocess.run(
        ["git", "-C", str(ROOT), "merge-base", "--is-ancestor",
         freeze["base_commit"], head], check=False)
    if ancestry.returncode:
        errors.append("audit_base_not_ancestor")

    original = load(PKG / "provenance/original-freeze-7881.json")
    input_path = ROOT / freeze["raw_path"]
    if sha256(input_path.read_bytes()) != freeze["raw_sha256"]:
        errors.append("raw_hash_mismatch")
    candidate_path = ROOT / freeze["candidate_copy_path"]
    if sha256(candidate_path.read_bytes()) != freeze["candidate_sha256"]:
        errors.append("candidate_copy_hash_mismatch")
    original_path = ROOT / freeze["original_freeze_copy_path"]
    if sha256(original_path.read_bytes()) != freeze["original_freeze_sha256"]:
        errors.append("original_freeze_hash_mismatch")
    if (freeze["candidate_sha256"] != original.get("source_sha256", {}).get(
            "research/doom/map01_v39_startup_release_order_a01_20261005/candidate.py")):
        errors.append("original_candidate_lock_mismatch")
    original_source_commit = original.get("base_commit")
    for rel, expected in original.get("source_sha256", {}).items():
        if rel.endswith("/candidate.py"):
            source_bytes = candidate_path.read_bytes()
        elif rel.endswith("/PLAN.md"):
            source_bytes = (PKG / "provenance/plan-7881-a03.md").read_bytes()
        else:
            source = subprocess.run(
                ["git", "-C", str(ROOT), "show", f"{original_source_commit}:{rel}"],
                check=False, capture_output=True)
            if source.returncode:
                errors.append("historical_source_missing:" + rel)
                continue
            source_bytes = source.stdout
        if sha256(source_bytes) != expected:
            errors.append("historical_source_hash:" + rel)
    for rel, expected in freeze["source_sha256"].items():
        path = ROOT / rel
        if not path.is_file() or sha256(path.read_bytes()) != expected:
            errors.append("source_hash:" + rel)
        if original.get("source_sha256", {}).get(rel) != expected:
            errors.append("original_source_lock:" + rel)
    auditor_path = Path(__file__).resolve()
    if sha256(auditor_path.read_bytes()) != freeze.get("auditor_sha256"):
        errors.append("auditor_hash_mismatch")
    plan_path = PKG / "PLAN.md"
    if sha256(plan_path.read_bytes()) != freeze.get("plan_sha256"):
        errors.append("plan_hash_mismatch")
    return errors, head, original


def identity(row):
    return (row.get("id"), row.get("intent_token"), row.get("owner_id"),
            row.get("key"), row.get("step"))


def reconstruct(raw):
    errors = []
    events = raw.get("events")
    ops = raw.get("operations")
    if type(events) is not list or type(ops) is not list:
        return ["events_or_operations_missing"], []

    admissions = [row for row in events if row.get("event") == "input_admission"]
    releases = [row for row in events if row.get("event") == "input_release_transition"]
    if len(admissions) != 2 or len(releases) != 2:
        errors.append("edge_cardinality")
    if len({identity(row) for row in admissions}) != len(admissions):
        errors.append("duplicate_admission_identity")
    if len({identity(row) for row in releases}) != len(releases):
        errors.append("duplicate_release_identity")

    # These keycodes are part of the frozen fake-display harness in candidate.py.
    keycodes = {"F8": 74, "SPACE": 65}
    joins = []
    used_release_ids = set()
    for admission in admissions:
        key = identity(admission)
        matches = [row for row in releases if identity(row) == key]
        if len(matches) != 1:
            errors.append("admission_release_join_count:" + str(admission.get("key")))
            continue
        release = matches[0]
        release_index = releases.index(release)
        used_release_ids.add(release_index)
        receipt = release.get("owner_thread_keyup_receipt")
        if type(receipt) is not dict:
            errors.append("owner_receipt_missing:" + str(admission.get("key")))
            continue
        for field in ("intent_token", "owner_id", "key"):
            if receipt.get(field) != admission.get(field):
                errors.append("owner_receipt_identity:" + field + ":" + str(admission.get("key")))
        if release.get("valid_until_ns") != admission.get("valid_until_ns"):
            errors.append("lease_deadline_mismatch:" + str(admission.get("key")))
        if release.get("release_batch_identifier") != admission.get("id"):
            errors.append("batch_identifier_mismatch:" + str(admission.get("key")))
        if (release.get("owner_transition_verified") is not True or
                release.get("owner_thread_keyup_verified_after_batch") is not True or
                release.get("owner_identity_matches_after_batch") is not True or
                release.get("intent_token_matches_after_batch") is not True or
                release.get("owner_release_history_complete") is not True or
                release.get("owner_cleanup_intervened") is not False or
                release.get("release_batch_complete") is not True or
                release.get("release_batch_size") != 2 or
                release.get("release_batch_step") != admission.get("step")):
            errors.append("release_batch_contract:" + str(admission.get("key")))
        if receipt.get("valid_until_ns") != admission.get("valid_until_ns"):
            errors.append("owner_deadline_mismatch:" + str(admission.get("key")))
        if (release.get("owner_thread_keyup_verified") is not True or
                release.get("owner_thread_keyup_receipt_count") != 1 or
                receipt.get("server_sync_completed") is not True or
                receipt.get("physical_verification_authoritative") is not False):
            errors.append("owner_receipt_contract:" + str(admission.get("key")))

        code = keycodes.get(admission.get("key"))
        if type(code) is not int or receipt.get("keycode") != code:
            errors.append("keycode_identity:" + str(admission.get("key")))
        down_ops = [op for op in ops if op.get("op") == "key-down" and op.get("keycode") == code]
        up_ops = [op for op in ops if op.get("op") == "key-up" and op.get("keycode") == code]
        if len(down_ops) != 1 or len(up_ops) != 1:
            errors.append("operation_edge_count:" + str(admission.get("key")))
            continue
        down = down_ops[0]
        up = up_ops[0]
        try:
            down_index = ops.index(down)
            up_index = ops.index(up)
            down_sync = ops[down_index + 1]
            up_sync = ops[up_index + 1]
        except IndexError:
            errors.append("sync_operation_missing:" + str(admission.get("key")))
            continue
        if down_sync.get("op") != "sync" or up_sync.get("op") != "sync":
            errors.append("sync_operation_order:" + str(admission.get("key")))
        down_bounds = (admission.get("admitted_ns"), down.get("at_ns"),
                       down_sync.get("at_ns"), admission.get("input_ack_ns"))
        release_bounds = (release.get("release_call_started_ns"),
                          receipt.get("owner_keyrelease_started_ns"), up.get("at_ns"),
                          up_sync.get("at_ns"), receipt.get("owner_sync_returned_ns"),
                          release.get("release_call_returned_ns"))
        if not all(type(value) is int for value in down_bounds + release_bounds):
            errors.append("timestamp_missing:" + str(admission.get("key")))
        elif not all(a <= b for a, b in zip(down_bounds, down_bounds[1:])):
            errors.append("down_timestamp_order:" + str(admission.get("key")))
        elif not all(a <= b for a, b in zip(release_bounds, release_bounds[1:])):
            errors.append("release_timestamp_order:" + str(admission.get("key")))
        elif admission["input_ack_ns"] > release["release_call_started_ns"]:
            errors.append("down_release_bracket_overlap:" + str(admission.get("key")))
        joins.append({
            "identity": {"id": admission.get("id"), "intent_token": admission.get("intent_token"),
                         "owner_id": admission.get("owner_id"), "key": admission.get("key"),
                         "step": admission.get("step")},
            "keycode": code,
            "admission_ack_to_release_call_start_ns": (
                release.get("release_call_started_ns", 0) - admission.get("input_ack_ns", 0)),
            "down_request_bracket_ns": [admission.get("admitted_ns"), admission.get("input_ack_ns")],
            "release_request_bracket_ns": [release.get("release_call_started_ns"),
                                           release.get("release_call_returned_ns")],
            "owner_keyup_sync_bracket_ns": [receipt.get("owner_keyrelease_started_ns"),
                                            receipt.get("owner_sync_returned_ns")],
            "physical_occupancy_interval_observed": False,
            "independent_task_effect_interval_observed": False,
        })
    if len(used_release_ids) != len(releases):
        errors.append("unmatched_release_rows")

    expected_order = ["SPACE", "F8"]
    if [row.get("key") for row in releases] != expected_order:
        errors.append("release_key_order")
    if [row.get("release_batch_position") for row in releases] != [0, 1]:
        errors.append("release_batch_position_order")
    up_indexes = [index for index, op in enumerate(ops) if op.get("op") == "key-up"]
    if len(up_indexes) != 2:
        errors.append("key_up_operation_count")
        between = []
    else:
        between = ops[up_indexes[0] + 1:up_indexes[1]]
        if any(op.get("op") == "query_keymap" for op in between):
            errors.append("query_keymap_between_ups")
    if between != raw.get("between_up_operations"):
        errors.append("between_up_raw_copy_mismatch")
    if raw.get("keymap_queries_between_ups") != 0:
        errors.append("keymap_query_summary_mismatch")
    if raw.get("fake_physical_after") != [] or raw.get("backend_held_after") != []:
        errors.append("fake_final_state_not_empty")

    return errors, joins


def mutation_controls(raw):
    controls = {}
    changed = copy.deepcopy(raw)
    next(row for row in changed["events"] if row.get("event") == "input_release_transition")["intent_token"] = "wrong-intent"
    controls["mismatched_release_intent_rejected"] = bool(reconstruct(changed)[0])

    changed = copy.deepcopy(raw)
    first = next(row for row in changed["events"] if row.get("event") == "input_release_transition")
    changed["events"].append(copy.deepcopy(first))
    controls["duplicate_release_rejected"] = bool(reconstruct(changed)[0])

    changed = copy.deepcopy(raw)
    first = next(row for row in changed["events"] if row.get("event") == "input_release_transition")
    first["owner_thread_keyup_receipt"]["owner_sync_returned_ns"] = 1
    controls["reversed_receipt_chronology_rejected"] = bool(reconstruct(changed)[0])

    changed = copy.deepcopy(raw)
    first = next(row for row in changed["operations"] if row.get("op") == "key-up")
    first["keycode"] = 999
    controls["wrong_keycode_rejected"] = bool(reconstruct(changed)[0])
    return controls


def audit():
    freeze = load(PKG / "FREEZE.json")
    freeze_errors, head, original = verify_freeze(freeze)
    raw = load(ROOT / freeze["raw_path"])
    reconstruction_errors, joins = reconstruct(raw)
    mutations = mutation_controls(raw)
    errors = freeze_errors + reconstruction_errors
    if not all(mutations.values()):
        errors.append("mutation_control_not_detected")

    # Contextual identity is unique only for this two-distinct-key trace.
    has_actuation_id = any("actuation_id" in row for row in raw.get("events", []))
    effect_rows = [row for row in raw.get("events", [])
                   if "effect" in str(row.get("event", "")).lower()]
    effect_link = all(row["independent_task_effect_interval_observed"] for row in joins)
    join_pass = not freeze_errors and not reconstruction_errors and all(mutations.values())
    instrumentation_pass = join_pass and effect_link
    return {
        "schema": "v39-startup-edge-identity-audit-result-v1",
        "base_commit": head,
        "source_trace_commit": original.get("base_commit"),
        "source_trace_pr_head": freeze["base_pr_head"],
        "identity_join_subcheck": "PASS_CONTEXTUAL_JOIN_ONLY" if join_pass else "FAIL",
        "instrumentation_gate": "PASS_INSTRUMENTATION" if instrumentation_pass
                               else "HOLD_EFFECT_LINK" if join_pass else "FAIL",
        "disposition": "HOLD_LIVE_EFFECT_LINK" if join_pass and not effect_link
                       else "PASS_INSTRUMENTATION" if instrumentation_pass else "FAIL",
        "errors": errors,
        "joins": joins,
        "join_count": len(joins),
        "mutation_controls": mutations,
        "actuation_id_present": has_actuation_id,
        "independent_effect_rows_present": bool(effect_rows),
        "independent_task_effect_interval_linked": effect_link,
        "raw_inter_up_operations": raw.get("between_up_operations"),
        "raw_keymap_queries_between_ups": raw.get("keymap_queries_between_ups"),
        "scope": "posthoc identity/timestamp audit of one deterministic fake-X V39 startup trace; contextual (not actuation-ID) pairing of two distinct keys",
        "limits": [
            "No actuation_id is recorded, so repeated same-key actuations within one intent/step could not be distinguished by this contextual join.",
            "XTest/XSync request timing is not an authoritative physical key-occupancy interval.",
            "The trace has no independently observed task-effect interval and cannot support useful-feedback or MAP01 claims.",
            "No live X11, DoomGame, model, OS input, formal allocation, or candidate rerun occurred.",
        ],
    }


if __name__ == "__main__":
    result = audit()
    out = PKG / "results/AUDIT.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(bool(result["errors"]))
