"""Independent, read-only reconstruction of merged PR #7599 raw evidence."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PACKAGE = REPO / "research/doom/game_action_sampling_59_4d74_20261004"
RUN = PACKAGE / "construction03"
SOURCE_COMMIT = "4c2fe6cbd4218306bcb203cf04258b0f9a322213"
LEFT_VECTOR = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def action_reconstruction(rows: list[dict]) -> dict:
    active_indices = [i for i, row in enumerate(rows) if any(value != 0 for value in row["action"])]
    if not active_indices:
        return {"active_indices": [], "checks": {"one_left_vector": False, "contiguous": False}}
    first, last = active_indices[0], active_indices[-1]
    vector_ok = all(rows[i]["action"] == LEFT_VECTOR for i in active_indices)
    neutral_before = all(value == 0 for value in rows[first - 1]["action"])
    neutral_after = all(value == 0 for value in rows[last + 1]["action"])
    indices_contiguous = active_indices == list(range(first, last + 1))
    return {
        "active_indices": active_indices,
        "first_index": first,
        "last_index": last,
        "checks": {
            "one_left_vector": vector_ok,
            "contiguous": indices_contiguous,
            "neutral_before": neutral_before,
            "neutral_after": neutral_after,
        },
    }


def release_order_ok(last_active: dict, release: dict, first_neutral: dict) -> bool:
    receipt = release.get("owner_thread_keyup_receipt", {})
    return all((
        last_active["sample_returned_ns"] < receipt.get("owner_keyrelease_started_ns", 0),
        release.get("release_call_started_ns", 0) <= receipt.get("owner_keyrelease_started_ns", 0),
        receipt.get("owner_sync_returned_ns", 0) <= release.get("release_call_returned_ns", 0),
        release.get("owner_sample_after_finished_ns", 0) <= first_neutral["sample_started_ns"],
        receipt.get("server_sync_completed") is True,
        release.get("owner_transition_verified") is True,
        receipt.get("owner_id") == release.get("owner_id"),
        receipt.get("intent_token") == release.get("intent_token"),
        release.get("owner_thread_keyup_history_complete") is True,
        receipt.get("physical_verification_authoritative") is False,
        release.get("physical_verification_authoritative") is False,
        release.get("owned_keycodes_after_batch") == [],
        release.get("owner_thread_keyup_verified_after_batch") is True,
    ))


def validate_source_records(members: dict, tree: dict, blobs: dict[bytes, bytes]) -> dict:
    git_blob_failures = []
    sha256_failures = []
    byte_count_failures = []
    for path, row in members.items():
        object_id = tree.get(path)
        if object_id != row["git_blob"]:
            git_blob_failures.append(path)
        data = blobs.get(object_id.encode("ascii")) if object_id else None
        if data is None or hashlib.sha256(data).hexdigest() != row["sha256"]:
            sha256_failures.append(path)
        if data is None or len(data) != row["bytes"]:
            byte_count_failures.append(path)
    return {
        "git_blob_failures": git_blob_failures,
        "sha256_failures": sha256_failures,
        "byte_count_failures": byte_count_failures,
    }


def source_tree_pins_ok(preparation: dict) -> tuple[int, dict]:
    output = subprocess.run(
        ["git", "ls-tree", "-r", "-z", preparation["source_commit"]],
        cwd=REPO, check=True, capture_output=True,
    ).stdout
    tree = {}
    for record in output.split(b"\0"):
        if not record:
            continue
        metadata, path = record.split(b"\t", 1)
        _mode, kind, object_id = metadata.split()
        if kind == b"blob":
            tree[path.decode("utf-8")] = object_id.decode("ascii")
    object_ids = sorted({tree[path] for path in preparation["members"] if path in tree})
    batch = subprocess.run(
        ["git", "cat-file", "--batch"], cwd=REPO, check=True,
        input=("\n".join(object_ids) + "\n").encode("ascii"), capture_output=True,
    ).stdout
    blobs = {}
    offset = 0
    while offset < len(batch):
        header_end = batch.index(b"\n", offset)
        object_id, kind, size_text = batch[offset:header_end].split()
        size = int(size_text)
        data_start = header_end + 1
        data_end = data_start + size
        if kind != b"blob" or batch[data_end:data_end + 1] != b"\n":
            raise ValueError("unexpected git cat-file --batch record")
        blobs[object_id] = batch[data_start:data_end]
        offset = data_end + 1
    return len(tree), validate_source_records(preparation["members"], tree, blobs)


def run_audit() -> dict:
    manifest = read_json(PACKAGE / "FILES.json")["members"]
    manifest_failures = []
    actual_files = {
        p.relative_to(PACKAGE).as_posix()
        for p in PACKAGE.rglob("*") if p.is_file()
    }
    if actual_files - set(manifest) != {"FILES.json"}:
        manifest_failures.append("manifest_membership")
    for rel, row in manifest.items():
        data = (PACKAGE / rel).read_bytes()
        if len(data) != row["bytes"] or hashlib.sha256(data).hexdigest() != row["sha256"]:
            manifest_failures.append(rel)

    preparation = read_json(PACKAGE / "SOURCE_PREPARATION.json")
    tree_blob_count, source_pin_checks = source_tree_pins_ok(preparation)
    declared_copies = read_json(PACKAGE / "DECLARED_COPIES.json")
    copy_failures = []
    for rel in declared_copies:
        source = PACKAGE / "source" / "research" / rel
        pin = preparation["members"].get("research/" + rel)
        if (not source.is_file() or pin is None or
                hashlib.sha256(source.read_bytes()).hexdigest() != pin["sha256"]):
            copy_failures.append(rel)

    rows = read_jsonl(RUN / "scorer-last-action.jsonl")
    action = action_reconstruction(rows)
    active = action["active_indices"]
    first_idx, last_idx = active[0], active[-1]
    before, first = rows[first_idx - 1], rows[first_idx]
    last, after = rows[last_idx], rows[last_idx + 1]
    row_shape_ok = all(
        row.get("event") == "scorer_last_action" and row.get("authority") is False and
        row.get("coherent_tic") is True and row.get("tic_before") == row.get("tic_after") and
        row.get("buttons") == rows[0].get("buttons") and len(row.get("action", [])) == 9
        for row in rows
    )
    saved_audit = read_json(RUN / "SAVED_ACTION_AUDIT.json")
    saved_rows_match = all(
        saved_audit[key] == row
        for key, row in (("before", before), ("first_active", first),
                         ("last_active", last), ("first_neutral_after", after))
    )

    events_path = RUN / "runtime/events.jsonl"
    event_bytes = events_path.read_bytes()
    delivery_bytes = (RUN / "runtime/delivered.jsonl").read_bytes()
    stdout_bytes = (RUN / "session.stdout.jsonl").read_bytes()
    events = read_jsonl(events_path)
    release_rows = [e for e in events if e.get("event") == "input_release_transition"]
    release = release_rows[0] if len(release_rows) == 1 else {}
    admission_rows = [e for e in events if e.get("event") == "input_admission"]
    held_rows = [e for e in events if e.get("event") == "keys_held"]
    admission = admission_rows[0] if len(admission_rows) == 1 else {}
    held = held_rows[0] if len(held_rows) == 1 else {}
    progress = read_jsonl(RUN / "runtime/scorer-samples.jsonl")
    client_updates = read_jsonl(RUN / "runtime/scorer-client-updates.jsonl")
    progress_links_ok = len(progress) == len(client_updates) and all(
        client["sample"] == sample["payload"] and
        client["sample_sequence"] == sample["payload"]["producer"]["sample_sequence"]
        for sample, client in zip(progress, client_updates)
    )
    no_task_effect = all(
        sample["payload"]["death_count"] == 0 and
        sample["payload"]["kill_count"] == 0 and
        sample["payload"]["player_dead"] is False and
        sample["payload"]["map_exit"] is False and
        sample["payload"]["episode_finished"] is False
        for sample in progress
    )
    probe_final = read_json(RUN / "PROBE_FINAL.json")
    normal_finish = any(
        e.get("event") in {"post_control_score", "final_score"} for e in events
    )
    protocol_stop_retained = (
        probe_final.get("child_exit") == -9 and
        probe_final.get("external_rescue_used") is True and
        probe_final.get("reader_alive") is True and not normal_finish
    )
    release_ok = len(release_rows) == 1 and release_order_ok(last, release, after)
    input_to_sample_ok = (
        len(admission_rows) == len(held_rows) == 1 and
        admission.get("key") == held.get("keys", [None])[0] == release.get("key") == "Left" and
        admission.get("id") == held.get("id") == release.get("id") == "left-action-probe" and
        admission.get("intent_token") == release.get("intent_token") and
        held.get("input_ack_ns", 0) < first["sample_started_ns"] and
        last["sample_returned_ns"] < release.get("owner_thread_keyup_receipt", {}).get("owner_keyrelease_started_ns", 0)
    )
    coherent_count = sum(
        row.get("coherent_tic") is True and row.get("tic_before") == row.get("tic_after")
        for row in rows
    )
    action_ticks = [rows[i]["tic_before"] for i in active]
    all_checks = {
        "package_manifest_89_members": not manifest_failures and len(manifest) == 89,
        "source_preparation_git_pins": not source_pin_checks["git_blob_failures"] and len(preparation["members"]) == 1957,
        "source_preparation_sha256_and_byte_counts": (
            not source_pin_checks["sha256_failures"] and
            not source_pin_checks["byte_count_failures"] and len(preparation["members"]) == 1957
        ),
        "declared_source_copies": not copy_failures and len(declared_copies) == 20,
        "sample_rows_authority_free_and_tic_coherent": row_shape_ok and len(rows) == 717 and coherent_count == 717,
        "left_action_only_with_neutral_neighbors": all(action["checks"].values()) and len(active) == 8,
        "saved_posthoc_selected_rows_reconstructed": saved_rows_match,
        "admitted_left_action_brackets_sampled_left_interval": input_to_sample_ok,
        "release_receipt_ordered_between_samples": release_ok,
        "event_delivery_and_session_stdout_byte_equal": event_bytes == delivery_bytes == stdout_bytes,
        "progress_samples_linked_and_no_task_effect": progress_links_ok and len(progress) == 715 and no_task_effect,
        "cleanup_stop_not_misgraded_as_normal_finish": protocol_stop_retained,
    }
    passed = all(all_checks.values())
    return {
        "schema": "game-action-sampling-independent-audit-v1",
        "source_commit": preparation["source_commit"],
        "manifest_member_count": len(manifest),
        "source_pin_count": len(preparation["members"]),
        "source_sha256_pin_count": len(preparation["members"]) - len(source_pin_checks["sha256_failures"]),
        "source_byte_count_pin_count": len(preparation["members"]) - len(source_pin_checks["byte_count_failures"]),
        "source_tree_blob_count": tree_blob_count,
        "declared_copy_count": len(declared_copies),
        "action_sample_count": len(rows),
        "coherent_action_sample_count": coherent_count,
        "active_sample_count": len(active),
        "active_sample_tics": action_ticks,
        "before_tic": before["tic_before"],
        "after_tic": after["tic_before"],
        "first_active_sample_started_ns": first["sample_started_ns"],
        "last_active_sample_started_ns": last["sample_started_ns"],
        "owner_keyup_started_ns": release.get("owner_thread_keyup_receipt", {}).get("owner_keyrelease_started_ns"),
        "owner_xsync_returned_ns": release.get("owner_thread_keyup_receipt", {}).get("owner_sync_returned_ns"),
        "first_neutral_after_sample_started_ns": after["sample_started_ns"],
        "progress_sample_count": len(progress),
        "task_effect_observed": not no_task_effect,
        "normal_finish": normal_finish,
        "external_rescue_used": probe_final.get("external_rescue_used"),
        "reader_alive_after_probe": probe_final.get("reader_alive"),
        "checks": all_checks,
        "disposition": {
            "sampled_game_action_state": "PASS_SAMPLED_GAME_ACTION_STATE_SCOPED" if passed else "FAIL_AUDIT",
            "protocol_completion": "STOP_PROTOCOL_COMPLETION" if protocol_stop_retained else "UNVERIFIED",
            "useful_game_effect_or_recovery": "NOT_DEMONSTRATED",
            "exact_physical_or_engine_transition_onset": "NOT_IDENTIFIED",
        },
        "limits": [
            "Scorer last-action rows are sampled observations, not an exact engine transition trace.",
            "The owner-thread receipt proves ordered XTest KeyRelease/XSync and empty owned-key sample, not physical or game-effect release.",
            "Progress samples report no kill, death, map exit, or episode completion; this action probe is not a gameplay success or recovery test.",
            "The later protocol timed out, killed its direct child, left the reader alive, and used external rescue; retain STOP_PROTOCOL_COMPLETION.",
        ],
    }


def main() -> int:
    result = run_audit()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if all(result["checks"].values()) else 1


if __name__ == "__main__":
    sys.exit(main())
