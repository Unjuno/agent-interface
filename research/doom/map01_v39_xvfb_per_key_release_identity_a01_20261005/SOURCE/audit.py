"""Independent raw-only audit of Xvfb per-key release identity evidence."""
import argparse
import hashlib
import json
from pathlib import Path


PATTERN = [
    ("a", True), ("a", False),
    ("a", True), ("a", False),
    ("a", True), ("space", True), ("space", False), ("a", False),
]


def expected(cycles):
    actions = []
    states = {"a": False, "space": False}
    for cycle in range(cycles):
        for edge, (key, down) in enumerate(PATTERN):
            states[key] = down
            actions.append({
                "cycle": cycle, "edge": edge, "key": key, "down": down,
                "keymap": dict(states),
            })
    return actions


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(raw, freeze):
    checks = {}
    errors = []
    cycles = freeze["cycles"]
    executor_id = freeze["executor_identifier"]
    executor_step = freeze["executor_step"]
    wanted = expected(cycles)
    source_dir = Path(__file__).resolve().parent / "source"
    checks["bundled_sources_match_freeze"] = all(
        (source_dir / name).is_file() and sha(source_dir / name) == digest
        for name, digest in freeze["source_sha256"].items()
    )
    checks["candidate_and_auditor_match_freeze"] = (
        sha(Path(__file__).with_name("candidate.py")) == freeze["candidate_sha256"]
        and sha(__file__) == freeze["auditor_sha256"]
        and raw.get("candidate_sha256") == freeze["candidate_sha256"]
    )
    checks["raw_source_manifest_matches_freeze"] = raw.get("source_sha256") == freeze["source_sha256"]
    checks["candidate_completed"] = raw.get("status") == "CANDIDATE_COMPLETE"
    checks["requested_cycle_count"] = raw.get("cycles_requested") == cycles
    checks["all_server_keymap_edges_match"] = raw.get("actions") == [
        {k: v for k, v in row.items() if k in ("key", "down", "keymap")}
        for row in wanted
    ]

    event_rows = raw.get("client_events")
    expected_events = []
    keycodes = raw.get("keycodes")
    for action in wanted:
        expected_events.append({
            "cycle": action["cycle"], "edge": action["edge"],
            "key": action["key"], "down": action["down"],
            "event_type": 2 if action["down"] else 3,
            "keycode": keycodes.get(action["key"]) if isinstance(keycodes, dict) else None,
        })
    checks["client_events_match_each_edge"] = isinstance(event_rows, list) and len(event_rows) == len(expected_events)
    if checks["client_events_match_each_edge"]:
        for got, want in zip(event_rows, expected_events):
            if any(got.get(key) != value for key, value in want.items()):
                checks["client_events_match_each_edge"] = False
                break
    dispatch_ns = [row.get("dispatch_ns") for row in event_rows or []]
    checks["client_dispatch_clock_ordered"] = (
        len(dispatch_ns) == len(expected_events)
        and all(type(value) is int for value in dispatch_ns)
        and all(left <= right for left, right in zip(dispatch_ns, dispatch_ns[1:]))
    )

    rows = raw.get("emitted_rows")
    admissions = [row for row in rows or [] if row.get("event") == "input_admission"]
    releases = [row for row in rows or [] if row.get("event") == "input_release_transition"]
    checks["admission_count"] = len(admissions) == cycles * 4
    checks["release_count"] = len(releases) == cycles * 4
    admission_by_identity = {}
    for position, row in enumerate(admissions):
        identity = (row.get("id"), row.get("step"), row.get("admission_position"))
        if identity != (executor_id, executor_step, position) or identity in admission_by_identity:
            errors.append(f"invalid or duplicate admission identity at row {position}")
        admission_by_identity[identity] = row
    checks["admission_ordinals_are_unique_and_ordered"] = not errors

    seen_releases = set()
    release_ok = True
    for row in releases:
        identity = (row.get("id"), row.get("step"), row.get("admission_position"))
        admission = admission_by_identity.get(identity)
        if (admission is None or identity in seen_releases
                or admission.get("key") != row.get("key")
                or row.get("admission_identity_status") != "matched"
                or row.get("release_key_matches_request") is not True
                or row.get("owner_transition_verified") is not True
                or row.get("release_batch_keys_match_requests") is not True):
            release_ok = False
            errors.append(f"release identity/verification mismatch for {identity!r}")
        seen_releases.add(identity)
    checks["every_release_matches_one_exact_key_admission"] = (
        release_ok and seen_releases == set(admission_by_identity)
    )
    checks["batch_authority_is_exact_and_non_authoritative"] = all(
        row.get("owner_identity_matches_after_batch") is True
        and row.get("intent_token_matches_after_batch") is True
        and row.get("owner_sample_ordered_after_batch") is True
        and row.get("owned_keycodes_after_batch") == []
        and row.get("physical_verification_authoritative") is False
        and row.get("grants_input_authority") is False
        for row in releases
    ) and len(releases) == cycles * 4

    batches = {}
    for row in releases:
        batch = (row.get("release_batch_identifier"), row.get("release_batch_step"),
                 row.get("owner_sample_after_finished_ns"))
        batches.setdefault(batch, []).append(row)
    sizes = [len(batch) for batch in batches.values()]
    checks["release_batch_sizes_match_sequence"] = sizes == [1, 1, 2] * cycles
    checks["release_batch_positions_are_complete"] = all(
        sorted(row.get("release_batch_position") for row in batch)
        == list(range(len(batch)))
        and all(row.get("release_batch_size") == len(batch) for row in batch)
        for batch in batches.values()
    )

    cleanup = raw.get("cleanup") or {}
    checks["server_keymap_empty_after_edges_and_close"] = (
        raw.get("server_keymap_empty_after_edges") is True
        and cleanup.get("server_keymap_empty_after_close") is True
    )
    release = cleanup.get("explicit_owner_release")
    close = cleanup.get("owner_close_result")
    checks["owner_empty_release_and_close_verified"] = (
        isinstance(release, dict) and release.get("verified") is True
        and release.get("keys_down") == []
        and isinstance(close, dict) and close.get("verified") is True
        and close.get("keys_down") == []
        and cleanup.get("owner_closed") is True
        and cleanup.get("owner_stopped") is True
        and cleanup.get("owner_thread_alive") is False
    )
    checks["xvfb_stopped"] = cleanup.get("xvfb_stopped") is True
    checks["raw_has_no_candidate_errors"] = raw.get("errors") == []
    status = "PASS_METHOD_SCOPED" if all(checks.values()) else "FAIL"
    return {
        "schema": "map01-v39-xvfb-per-key-release-audit-a01-v1",
        "status": status,
        "checks": checks,
        "errors": errors,
        "admissions": len(admissions),
        "releases": len(releases),
        "client_events": len(event_rows) if isinstance(event_rows, list) else None,
        "scope": "local Xvfb/InputOwner/client event boundary only; no application or task effect",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True)
    parser.add_argument("--freeze", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    raw = json.loads(Path(args.raw).read_text(encoding="utf-8"))
    freeze = json.loads(Path(args.freeze).read_text(encoding="utf-8"))
    result = run(raw, freeze)
    Path(args.out).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS_METHOD_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
