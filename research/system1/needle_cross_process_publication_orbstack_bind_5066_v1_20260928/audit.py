"""Independent raw-byte auditor; intentionally imports no runner/protocol code."""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import sys

OUT = Path("/out")
OLD, NEW, READERS, PHASES, SNAPSHOTS = 3788, 3789, 4, 7, 32
OLD_SHA = "2e7bff5a2c6ffd35935c5e3c88d08cb686fb736d332c8d5cdb24bb1b67dc873a"
IMAGE = "sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def overlap(a: int, b: int, intervals: list[dict]) -> bool:
    return any(a < x["end_ns"] and x["start_ns"] < b for x in intervals)


def audit(raw: object) -> list[str]:
    errors = []
    if not isinstance(raw, dict): return ["raw_not_object"]
    expected = {"allocation": "needle-publication-orbstack-bind-5066-20260928-01", "issue": 5073,
                "formal_invocations": 1, "image_id": IMAGE, "input_sha256": OLD_SHA,
                "input_git_blob": "45b80150dac503f4eb6f3cb5d82f9afa2c587107", "input_bytes": 15279,
                "dispatch_count": 0, "authority_granted": False, "construction": "0"}
    for k, v in expected.items():
        if raw.get(k) != v: errors.append("top_" + k)
    if raw.get("source_commit") != os.environ.get("OBSTAC_SOURCE_COMMIT"):
        errors.append("source_commit_env")
    if raw.get("freeze_sha256") != os.environ.get("OBSTAC_FREEZE_SHA256"):
        errors.append("freeze_sha_env")
    cand_sha = raw.get("candidate_raw_sha256")
    cand_n = raw.get("candidate_bytes")
    atomic = raw.get("atomic", {})
    unsafe = raw.get("unsafe", {})
    for arm_name, arm, prefix in (("atomic", atomic, "publish"), ("unsafe", unsafe, "write")):
        roster = arm.get("reader_pids")
        if not isinstance(roster, list) or len(roster) != READERS or len(set(roster)) != READERS:
            errors.append(arm_name + "_pid_roster"); continue
        if arm.get("pid") in roster: errors.append(arm_name + "_publisher_pid_collision")
        if arm.get("exit_codes") != [0] * READERS: errors.append(arm_name + "_exit_codes")
        rows = arm.get("rows")
        if not isinstance(rows, list) or len(rows) != PHASES * READERS:
            errors.append(arm_name + "_row_count"); continue
        seen = set()
        for record in rows:
            if not isinstance(record, dict): errors.append(arm_name + "_record_type"); continue
            phase, reader = record.get("phase"), record.get("reader")
            if not isinstance(phase, str) or not phase.startswith(prefix + "_") or reader not in range(READERS):
                errors.append(arm_name + "_phase_reader"); continue
            key = phase, reader
            if key in seen: errors.append(arm_name + "_duplicate_row")
            seen.add(key)
            if record.get("pid") != roster[reader]: errors.append(arm_name + "_pid_binding")
            snaps = record.get("rows")
            if not isinstance(snaps, list) or len(snaps) != SNAPSHOTS:
                errors.append(arm_name + "_snapshot_count"); continue
            if arm_name == "atomic":
                ints = [x for x in arm.get("replacement_intervals", []) if x.get("phase") == phase]
                if len(ints) != 64: errors.append("atomic_replace_count_" + phase)
                if not any(overlap(s.get("start_ns", 0), s.get("end_ns", 0), ints) for s in snaps):
                    errors.append("atomic_no_actual_overlap_" + phase)
                for s in snaps:
                    if s.get("generation") not in (OLD, NEW) or s.get("valid") is not True:
                        errors.append("atomic_incomplete_or_invalid_" + phase)
                    exp = raw.get("old_raw_sha256") if s.get("generation") == OLD else cand_sha
                    nbytes = raw.get("input_bytes") if s.get("generation") == OLD else cand_n
                    if s.get("raw_sha256") != exp or s.get("bytes") != nbytes:
                        errors.append("atomic_bytes_mismatch_" + phase)
            else:
                wi = next((x for x in arm.get("write_intervals", []) if x.get("phase") == phase), None)
                if wi is None or not any(s.get("start_ns", 0) < wi.get("end_ns", 0) and wi.get("start_ns", 0) < s.get("end_ns", 0) for s in snaps):
                    errors.append("unsafe_no_overlap_" + phase)
                if phase == "write_1" and not any(s.get("valid") is False and 0 < s.get("bytes", 0) < cand_n for s in snaps):
                    errors.append("unsafe_partial_not_observed")
    # Each replacement has exactly one post-publication row per persistent reader.
    posts = atomic.get("post_rows")
    if not isinstance(posts, list) or len(posts) != PHASES * READERS:
        errors.append("post_row_count")
    else:
        for row in posts:
            if row.get("pid") not in atomic.get("reader_pids", []): errors.append("post_pid")
            if any(s.get("valid") is not True or s.get("generation") != NEW or
                   s.get("raw_sha256") != cand_sha or s.get("bytes") != cand_n for s in row.get("rows", [])):
                errors.append("post_not_exact_candidate")
    if atomic.get("invalid_accepted") is not False or atomic.get("active_unchanged_rejections") is not True:
        errors.append("proposal_rejection_gate")
    if atomic.get("stale_disposition") != "YIELD_STALE_GENERATION": errors.append("stale_disposition")
    if atomic.get("active_before_rejection_sha256") != atomic.get("active_after_rejection_sha256"):
        errors.append("rejection_mutated_active")
    return errors


def corruption_controls(raw: dict) -> dict[str, bool]:
    mutations = {}
    x = copy.deepcopy(raw); x["dispatch_count"] = 1; mutations["dispatch"] = x
    x = copy.deepcopy(raw); x["atomic"]["rows"].pop(); mutations["missing_row"] = x
    x = copy.deepcopy(raw); x["atomic"]["replacement_intervals"][0]["end_ns"] = 0; mutations["no_overlap"] = x
    x = copy.deepcopy(raw); x["atomic"]["post_rows"][0]["rows"][0]["generation"] = OLD; mutations["wrong_post"] = x
    x = copy.deepcopy(raw)
    partial = next(r for r in x["unsafe"]["rows"] if r.get("phase") == "write_1")
    partial["rows"][0]["bytes"] = raw["candidate_bytes"]
    mutations["partial_length"] = x
    x = copy.deepcopy(raw); x["atomic"]["reader_pids"][0] = x["atomic"]["pid"]; mutations["pid_collision"] = x
    return {name: bool(audit(case)) for name, case in mutations.items()}


def main():
    path = OUT / "raw.json"
    raw = json.loads(path.read_text())
    errs = audit(raw)
    controls = corruption_controls(raw)
    report = {"status": "PASS_ORBSTACK_CROSS_PROCESS_PUBLICATION_SCOPED" if not errs and all(controls.values()) else "STOP_PROVENANCE_ENVIRONMENT_OR_AUDIT",
              "errors": errs, "corruption_controls": controls, "raw_sha256": digest(path.read_bytes()),
              "concurrent_batches": 56, "post_batches": 28, "snapshots_per_batch": SNAPSHOTS}
    (OUT / "audit.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"].startswith("PASS_") else 1


if __name__ == "__main__": raise SystemExit(main())
