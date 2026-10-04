"""Independent saved-result checks for the v39 fake-Xlib witness probe."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
row = json.loads((HERE / "result.json").read_text(encoding="utf-8"))
freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
occurrences = row.get("occurrences", [])
frozen_paths = freeze.get("sha256", {})
source_hashes_match = all(
    hashlib.sha256((HERE / name).read_bytes()).hexdigest() == expected
    for name, expected in frozen_paths.items()
)
checks = {
    "frozen_input_hashes_match": bool(frozen_paths) and source_hashes_match,
    "expected_main_and_source_lineage": (
        row.get("main_sha") == "13bab54ea6d91978247ecc1b70e5060db752367a"
        and row.get("owner_git_blob") == "341b3c01649943ddaad5f28431a792c4889cc36e"
        and row.get("wrapper_commit") == "0f112dcae1e3b108ae2eecddebd95b829b8fbffa"
        and row.get("wrapper_git_blob") == "e2e69b7f73d823b03e6a295e670f00189bb26778"
    ),
    "owner_source_hash_matches": hashlib.sha256(
        (HERE / "dependencies" / "input_owner_v10.py").read_bytes()).hexdigest()
        == row.get("owner_sha256") ==
        "ceae7d9983cd0ba13a35e01ce2ce7dbbf03a0397b23ddc123b0110b4d4de670b",
    "wrapper_source_hash_matches": hashlib.sha256(
        (HERE / "dependencies" / "input_transition_owner_v3.py").read_bytes()).hexdigest()
        == row.get("wrapper_sha256") ==
        "672e7471b91f321f0d8723ef6277d974b24b2fa322f5e89907b17bf92998f177",
    "two_distinct_occurrences": (
        len(occurrences) == 2
        and len({item.get("occurrence_id") for item in occurrences}) == 2
    ),
    "keymap_witnesses_are_32_bytes_and_match_bits": all(
        len(bytes.fromhex(item[name])) == 32
        and bool(bytes.fromhex(item[name])[item["keycode"] // 8]
                 & (1 << (item["keycode"] % 8))) is item[bit]
        for item in occurrences
        for name, bit in (("pre_down_keymap_hex", "pre_down"),
                          ("post_down_keymap_hex", "post_down"),
                          ("post_up_keymap_hex", "post_up"))
    ),
    "per_occurrence_false_true_false": all(
        (item.get("pre_down"), item.get("post_down"), item.get("post_up"))
        == (False, True, False) for item in occurrences
    ),
    "ordered_ack_and_release_bracket": all(
        type(item.get("owner_down_ack_ns")) is int
        and item["pre_down_sample_ns"] <= item["owner_down_ack_ns"]
        <= item["post_down_sample_ns"]
        and type(item.get("up_started_ns")) is int
        and item["up_started_ns"] <= item["up_returned_ns"]
        <= item["post_up_sample_ns"]
        for item in occurrences
    ),
    "v39_release_wrapper_accepts_both": all(
        item.get("admission_event") == "input_admission"
        and item.get("up_event") == "input_release_transition"
        and item.get("up_transition_schema") == "input-release-transition-v3"
        and item.get("ordinary_release_candidate") is True
        and item.get("owner_release_history_complete") is True
        for item in occurrences
    ),
    "terminal_cleanup_verified_empty": (
        len(row.get("owner_final_records", [])) == 1
        and row["owner_final_records"][0].get("event") == "owner_release"
        and row["owner_final_records"][0].get("verified") is True
        and row["owner_final_records"][0].get("keys_down") == []
    ),
    "scope_remains_non_authoritative_fake_xlib": (
        row.get("scope") ==
        "fake Xlib/XTest queue construction; not Xvfb, physical X11, or application effect"
        and all(item.get("witness_authority") is False for item in occurrences)
    ),
    "no_formal_or_live_allocation_claim": (
        freeze.get("allocation_id") is None
        and freeze.get("classification") == "construction-only"
        and freeze.get("live_candidate_invocations") == 0
    ),
}
for name, passed in checks.items():
    print(f"{'PASS' if passed else 'FAIL'} {name}")
if not all(checks.values()):
    raise SystemExit(1)
print(f"PASS {len(checks)} saved-result checks")
