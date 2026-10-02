#!/usr/bin/env python3
"""Independent raw-only oracle for the #5784 distinguishing-suffix fixture."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

RAW = Path("/work/out/formal.jsonl")
EXPECTED_SUFFIX = ["read", "navigate", "commit_scoped", "readback", "release"]
EXPECTED = {
    ("clean_reset", "history_a"): "target-committed",
    ("hidden_carryover", "history_a"): "target-committed",
    ("hidden_carryover", "history_b"): "wrong-target",
    ("known_bad_reset", "history_b"): "wrong-target",
    ("timing_only", "history_b"): "target-committed",
    ("missing_observation", "history_a"): "target-committed",
}


def canonical_genesis(anchor: str) -> dict:
    base = {"anchor": anchor, "seed": 17, "initial_visible": "screen-v1", "hidden": 0}
    digest = hashlib.sha256(json.dumps(base, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {**base, "identity_sha256": digest}


def assess(records: list[dict]) -> tuple[list[str], dict]:
    errors: list[str] = []
    headers = [r for r in records if r.get("kind") == "header"]
    rows = [r for r in records if r.get("kind") == "case"]
    if len(headers) != 1:
        return ["header_count"], {}
    header = headers[0]
    got_keys = [(r.get("kind"), r.get("history")) for r in rows]
    if len(rows) != 6 or len(set(got_keys)) != 6:
        errors.append("case_denominator_or_duplicate")
    by_key = {(r.get("kind"), r.get("history")): r for r in rows}
    if set(by_key) != set(EXPECTED):
        errors.append("case_set")
    for key, expected_effect in EXPECTED.items():
        row = by_key.get(key)
        if row is None:
            continue
        anchor = row.get("anchor")
        expected_anchor = "genesis_a" if row.get("history") == "history_a" else "genesis_b"
        if anchor != expected_anchor or row.get("genesis") != canonical_genesis(expected_anchor):
            errors.append("independent_genesis:" + repr(key))
        if row.get("suffix") != EXPECTED_SUFFIX:
            errors.append("common_suffix:" + repr(key))
        if row.get("post_reset_visible") != "screen-v1" or row.get("post_reset_seed") != 17:
            errors.append("visible_seed_initial_match:" + repr(key))
        outputs = row.get("outputs", [])
        release = next((x for x in outputs if x.get("step") == "release"), None)
        if not release or release.get("released") is not True:
            errors.append("release_not_verified:" + repr(key))
        readback = next((x for x in outputs if x.get("step") == "readback"), None)
        if key[0] == "missing_observation":
            if not readback or readback.get("observation") is not None:
                errors.append("missing_control_not_missing")
            if readback and readback.get("effect") is not None:
                errors.append("missing_control_invented_effect")
        elif not readback or readback.get("effect") != expected_effect:
            errors.append("suffix_effect:" + repr(key))
        if row.get("elapsed_ms", 10**9) > row.get("timing_tolerance_ms", -1):
            errors.append("timing_tolerance:" + repr(key))
    if header.get("formal_invocations") != 1 or header.get("reruns") != 0:
        errors.append("invocation_policy")
    if header.get("fresh_genesis_independent_of_candidate_reset") is not True:
        errors.append("genesis_independence_declaration")
    if len({r.get("genesis", {}).get("identity_sha256") for r in rows}) != 2:
        errors.append("genesis_identity_count")
    # The differentiating pair starts from independent genesis identities and
    # shares the exact suffix; only hidden history differs after bad reset.
    a = by_key.get(("hidden_carryover", "history_a"))
    b = by_key.get(("hidden_carryover", "history_b"))
    if a and b and a.get("outputs") == b.get("outputs"):
        errors.append("planted_divergence_not_detected")
    clean = by_key.get(("clean_reset", "history_a"))
    bad = by_key.get(("known_bad_reset", "history_b"))
    if clean and bad:
        ce = next((x.get("effect") for x in clean["outputs"] if x.get("step") == "readback"), None)
        be = next((x.get("effect") for x in bad["outputs"] if x.get("step") == "readback"), None)
        if ce == be:
            errors.append("known_bad_positive_control")
    timing = by_key.get(("timing_only", "history_b"))
    if timing and timing.get("elapsed_ms") != 47:
        errors.append("timing_only_control")
    return errors, {"rows": len(rows), "case_keys": sorted(map(str, by_key))}


def main() -> None:
    raw_bytes = RAW.read_bytes()
    records = [json.loads(line) for line in raw_bytes.decode("utf-8").splitlines()]
    errors, summary = assess(records)
    # Corruption controls must fail under the independent validator.
    mutations = {}
    bad = copy.deepcopy(records)
    next(r for r in bad if r.get("kind") == "hidden_carryover" and r.get("history") == "history_b")["outputs"][3]["effect"] = "target-committed"
    mutations["hidden_effect_flip_rejected"] = bool(assess(bad)[0])
    missing = [r for r in records if not (r.get("kind") == "hidden_carryover" and r.get("history") == "history_a")]
    mutations["dropped_row_rejected"] = bool(assess(missing)[0])
    bad_genesis = copy.deepcopy(records)
    next(r for r in bad_genesis if r.get("kind") == "clean_reset")["genesis"]["identity_sha256"] = "0" * 64
    mutations["genesis_corruption_rejected"] = bool(assess(bad_genesis)[0])
    bad_suffix = copy.deepcopy(records)
    next(r for r in bad_suffix if r.get("kind") == "clean_reset")["suffix"][0] = "unsafe_probe"
    mutations["suffix_corruption_rejected"] = bool(assess(bad_suffix)[0])
    if not all(mutations.values()):
        errors.append("mutation_control_escape")
    result = {
        "status": "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD_OR_EVIDENCE",
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        **summary,
        "errors": errors,
        "mutation_controls": mutations,
        "claim_boundary": "synthetic finite fixture only; no real GUI reset-equivalence claim",
    }
    (RAW.parent / "audit.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
