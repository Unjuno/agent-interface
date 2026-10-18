"""Independent raw-only auditor for the A04 current V39 release closure test."""
import argparse
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def audit(raw, freeze):
    errors = []
    def require(condition, message):
        if not condition:
            errors.append(message)

    require(raw.get("schema") == "map01-v39-xvfb-per-key-release-raw-a04-v1",
            "raw schema mismatch")
    require(raw.get("status") == "CANDIDATE_COMPLETE", "candidate did not complete")
    require(not raw.get("errors"), "candidate retained errors")
    actions = raw.get("actions")
    rows = raw.get("emitted_rows")
    admissions = [row for row in rows if row.get("event") == "input_admission"]
    releases = [row for row in rows if row.get("event") == "input_release_transition"]
    client = raw.get("client_events")
    require(raw.get("client_event_count") == 80 and len(client) == 80,
            "expected 80 client-dispatched edges")
    require(len(admissions) == 40, "expected 40 input admission rows")
    require(len(releases) == 40, "expected 40 release receipt rows")
    require(len(raw.get("batches", [])) == 30, "expected 30 completed release batches")
    require(len(raw.get("post_batch_keymaps", [])) == 30,
            "expected one external keymap sample after each batch")
    require(all(row.get("empty_after_batch") is True
                for row in raw.get("post_batch_keymaps", [])),
            "server keymap not empty after a completed batch")
    require(all(row.get("window") == raw.get("client_window") for row in client),
            "an X event reached an unexpected client window")
    require(all(row.get("keycode") == raw.get("keycodes", {}).get(row.get("key"))
                for row in client), "client event keycode mismatch")

    expected = []
    for cycle in range(10):
        expected.extend((cycle, batch_index, edge, key, down)
                        for batch_index, batch in enumerate(
                            [[("a", True), ("a", False)],
                             [("a", True), ("a", False)],
                             [("a", True), ("space", True),
                              ("space", False), ("a", False)]])
                        for edge, (key, down) in enumerate(batch))
    observed = [(row.get("cycle"), row.get("batch"), row.get("edge"),
                 row.get("key"), row.get("down")) for row in client]
    require(observed == expected, "X client edge order does not match frozen pattern")

    admission_keys = [(row.get("id"), row.get("step"), row.get("key"))
                      for row in admissions]
    require(len(set(admission_keys)) == len(admission_keys),
            "admission identity is duplicated")
    release_keys = [(row.get("id"), row.get("step"), row.get("key"))
                    for row in releases]
    require(sorted(admission_keys) == sorted(release_keys),
            "per-key release receipt does not join one admission")
    require(all(row.get("owner_thread_keyup_verified") is True and
                row.get("server_sync_completed") is True and
                row.get("physical_verification_authoritative") is False
                for row in releases), "release receipt flags violate contract")
    require(all(row.get("release_batch_complete") is True and
                row.get("owner_transition_verified") is True and
                row.get("owner_sample_ordered_after_batch") is True
                for row in releases), "release batch proof is incomplete")
    expected_batch_sizes = {index: (2 if index % 3 == 2 else 1)
                            for index in range(30)}
    actual_batch_sizes = {}
    for row in releases:
        actual_batch_sizes[row.get("step")] = actual_batch_sizes.get(row.get("step"), 0) + 1
    require(actual_batch_sizes == expected_batch_sizes,
            "one-key/two-key release batches have unexpected grouping")
    require(all(row.get("release_batch_size") == expected_batch_sizes.get(row.get("step"))
                for row in releases), "per-key batch position size disagrees")

    keyups = raw.get("owner_keyup_records", [])
    require(len(keyups) == 40, "expected 40 owner-thread explicit KeyRelease records")
    keyup_end = max((row.get("owner_sync_returned_ns", -1) for row in keyups),
                    default=-1)
    owner_queries = [row for row in raw.get("keymap_queries", [])
                     if row.get("role") == "owner_or_other"]
    require(len(owner_queries) == 1, "expected only the terminal owner keymap query")
    if owner_queries:
        require(owner_queries[0].get("started_ns", 0) >= keyup_end,
                "owner keymap query occurred before all explicit key-ups completed")
    require(raw.get("cleanup", {}).get("owner_closed") is True and
            raw.get("cleanup", {}).get("owner_stopped") is True and
            raw.get("cleanup", {}).get("owner_thread_alive") is False and
            raw.get("cleanup", {}).get("owner_keycodes_after_close") == [] and
            raw.get("cleanup", {}).get("xvfb_exit") == 0,
            "owner/Xvfb cleanup did not verify empty and stopped")
    return {"schema": "map01-v39-xvfb-per-key-release-audit-a04-v1",
            "candidate_sha256": freeze["candidate_sha256"],
            "raw_sha256": raw.get("candidate_sha256"),
            "assertions": {"expected_admissions": 40,
                           "actual_admissions": len(admissions),
                           "expected_release_receipts": 40,
                           "actual_release_receipts": len(releases),
                           "expected_client_edges": 80,
                           "actual_client_edges": len(client),
                           "release_join_count": sum(key in set(admission_keys)
                                                      for key in release_keys),
                           "keymap_queries_between_explicit_keyups": 0},
            "errors": errors,
            "decision": "PASS_METHOD_SCOPED" if not errors else "FAIL"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    freeze = json.loads(args.freeze.read_text())
    raw = json.loads(args.raw.read_text())
    if digest(args.candidate) != freeze["candidate_sha256"]:
        raise SystemExit("candidate SHA mismatch")
    result = audit(raw, freeze)
    result["raw_sha256"] = digest(args.raw)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"decision": result["decision"], "errors": result["errors"]}))
    if result["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
