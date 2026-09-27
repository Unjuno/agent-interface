"""Raw-only audit for the frozen Issue #3642 GTK allocation."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


EXPECTED_EVENTS = [
    {"kind": "obs", "id": "valid-gen1", "gen": 1, "seq": 1, "target": 1, "value": True},
    {"kind": "replace", "id": "replace-gen2", "gen": 2, "seq": 3, "target": 2},
    {"kind": "replace", "id": "delayed-replace-gen1", "gen": 1, "seq": 2, "target": 1},
    {"kind": "obs", "id": "stale-gen1", "gen": 1, "seq": 4, "target": 1, "value": True},
    {"kind": "obs", "id": "valid-gen2", "gen": 2, "seq": 5, "target": 2, "value": True},
]
EXPECTED = [
    [["emit", "valid-gen1"]],
    [["invalidate", 2, 2]],
    [["refuse_control", "replace", 2]],
    [["refuse", "stale-gen1"]],
    [["emit", "valid-gen2"]],
]


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def audit(evidence: Path) -> dict:
    errors: list[str] = []
    p = evidence / "allocation.json"
    if not p.is_file():
        return {"decision": "HOLD_OR_FAIL", "failures": ["allocation.json absent"]}
    a = json.loads(p.read_text())
    def check(ok: bool, name: str):
        if not ok:
            errors.append(name)

    check(a.get("schema") == "issue-3642/gtk-effect-allocation-v1", "schema")
    check(a.get("allocation_id") in ("issue3642-gtk-effect-01", "issue3642-preregister-smoke2-excluded"), "allocation id")
    check(a.get("container_image_id") == "sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27", "image digest")
    check(a.get("container_platform") == "linux/arm64", "platform")
    check(a.get("events") == EXPECTED_EVENTS, "event sequence")
    rows = a.get("prefixes", [])
    check(len(rows) == 5, "prefix count")
    observed_effects = []
    frame_hashes = []
    for i, row in enumerate(rows):
        check(row.get("index") == i + 1 and row.get("event") == EXPECTED_EVENTS[i], f"prefix {i+1} identity")
        check(row.get("candidate_delta") == EXPECTED[i], f"prefix {i+1} candidate delta")
        check(row.get("oracle_delta") == EXPECTED[i], f"prefix {i+1} oracle delta")
        check(row.get("state_equal") is True and row.get("candidate_state") == row.get("oracle_state"), f"prefix {i+1} state agreement")
        want_count = 1 if i < 4 else 2
        check(row.get("effect_count") == want_count and row.get("title") == f"resident-fixture:{want_count}", f"prefix {i+1} GUI count/title")
        raw_path = evidence / str(row.get("frame_path", ""))
        raw = raw_path.read_bytes() if raw_path.is_file() else b""
        check(bool(raw), f"prefix {i+1} raw frame present")
        check(len(raw) == row.get("bytes") and digest(raw) == row.get("sha256"), f"prefix {i+1} frame hash/length")
        check(row.get("width") == 320 and row.get("height") == 120, f"prefix {i+1} frame geometry")
        frame_hashes.append(digest(raw))
        if row.get("emitted"):
            observed_effects.append(row.get("event", {}).get("id"))
            kr = row.get("key_release") or {}
            check(kr.get("event_id") == row.get("event", {}).get("id") and kr.get("key") == "Space", f"prefix {i+1} key mapping")
            check(kr.get("verified_empty") is True and kr.get("keys_down") == [], f"prefix {i+1} release")
        else:
            check(row.get("key_release") is None, f"prefix {i+1} no synthetic key on non-emit")
    initial = a.get("initial", {})
    initial_raw_path = evidence / str(initial.get("frame_path", ""))
    initial_raw = initial_raw_path.read_bytes() if initial_raw_path.is_file() else b""
    check(bool(initial_raw) and len(initial_raw) == initial.get("bytes") and digest(initial_raw) == initial.get("sha256"), "initial raw frame hash/length")
    check(initial.get("title") == "resident-fixture:0" and initial.get("counter") == 0, "initial state")
    check(len(set([digest(initial_raw), *frame_hashes[:1]])) == 2, "first effect changed rendered frame")
    check(frame_hashes[0] == frame_hashes[1] == frame_hashes[2] == frame_hashes[3], "stale prefixes preserve rendered frame")
    check(frame_hashes[4] != frame_hashes[3], "final effect changed rendered frame")
    check(observed_effects == ["valid-gen1", "valid-gen2"], "emit-to-effect mapping")
    check(a.get("final_effect_count") == 2, "final effect count")
    check(a.get("candidate_state") == a.get("oracle_state"), "final candidate/oracle state")
    check(a.get("status") == "RUN_COMPLETED", "runner completion")
    check(a.get("fixture_exit_code") == 0 and a.get("fixture_reaped") is True, "fixture exit/reap")
    check(a.get("xvfb_exit_code") == 0 and a.get("xvfb_reaped") is True, "Xvfb exit/reap")
    check(a.get("x11_socket_removed") is True, "X11 socket cleanup")
    check(len(a.get("key_releases", [])) == 2 and all(x.get("verified_empty") and x.get("keys_down") == [] for x in a.get("key_releases", [])), "all physical releases")
    for log_name, hash_key in (("fixture.log", "fixture_log_sha256"), ("xvfb.log", "xvfb_log_sha256")):
        log_path = evidence / log_name
        check(log_path.is_file() and digest(log_path.read_bytes()) == a.get(hash_key), f"{log_name} retained hash")
    check(len(set((a.get("xvfb_pid"), a.get("fixture_pid")))) == 2, "distinct process identities")
    return {"decision": "PASS_TK_EVENT_WITNESS_AND_PUBLIC_MCP_CONTINUATION_SCOPED" if not errors else "HOLD_OR_FAIL", "checks": 33, "failures": errors,
            "allocation_id": a.get("allocation_id"), "frame_hashes": [digest(initial_raw), *frame_hashes],
            "candidate_source_sha256": "f2bc10dff9c2d5fdc0b066ad1ca38b690d68b1b21488bcfffe96373f695486df",
            "oracle_source_sha256": "fc1c15bbaeec5b94d01ed6b3b0c749525a72b2424f6cdd2d1d9d6c0089e82221"}


def main() -> int:
    evidence, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    result = audit(evidence)
    (out / "AUDIT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if not result["failures"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
