"""Independent audit of retained Issue #8406 A01 candidate bytes; no rerun."""
import copy
import hashlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURE_PATH = HERE.parent / "exception_preserving_skill_7418_t0_20261004" / "fixture.json"
RAW_PATH = (HERE.parent / "episodic_memory_schedule_8406_t0_a01_20261008"
            / "formal_01" / "RAW.json")
FIXTURE_SHA256 = "1c8b74dfdd8ec7c5a5950133709ae95e40cc687edb12ac128d66f696c79e54fb"
RAW_SHA256 = "2c79a10fa6530d74ac17ea9c67816b9517c63235a4cd32fcf70a2d463d4d9f70"
PREFIXES = (3, 6, 9, 12)
ARMS = ("episodic_only", "per_episode", "batch_4", "terminal")


def stable_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode()


def reconstruct(fixture):
    episodes = fixture["episodes"]
    ids = [row["id"] for row in episodes]
    digests = {row["id"]: hashlib.sha256(stable_bytes(row)).hexdigest()
               for row in episodes}
    oracle = {row["id"]: row["source_episode_ids"]
              for row in fixture["applicability_oracle"]}
    deps = {"heldout-04": oracle["ordinary-skill"],
            "protected-heldout": oracle["protected-exception"],
            "contradictory": oracle["ambiguous-conflict"],
            "unrepresented": []}
    points = {"episodic_only": [],
              "per_episode": list(range(1, len(ids) + 1)),
              "batch_4": [n for n in range(1, len(ids) + 1) if n % 4 == 0],
              "terminal": [len(ids)]}
    schedules = {}
    for arm in ARMS:
        updates = [{"after_episode": n,
                    "episode_refs": [{"id": eid, "sha256": digests[eid]}
                                     for eid in ids[:n]]}
                   for n in points[arm]]
        visibility = []
        for prefix in PREFIXES:
            due = [u for u in updates if u["after_episode"] <= prefix]
            available = (ids[:prefix] if arm == "episodic_only" else
                         [r["id"] for r in due[-1]["episode_refs"]] if due else [])
            last = due[-1]["after_episode"] if due else None
            for query, required in deps.items():
                found = [eid for eid in required if eid in available]
                state = ("NO_SOURCE_REQUIRED" if not required else
                         "FULL" if len(found) == len(required) else
                         "PARTIAL" if found else "NONE")
                visibility.append({"checkpoint": prefix,
                                   "latest_update_prefix": last,
                                   "query_id": query,
                                   "available_episode_ids": list(available),
                                   "required_source_ids": list(required),
                                   "retrieved_source_ids": found,
                                   "evidence_state": state})
        schedules[arm] = {"updates": updates, "query_visibility": visibility}
    return {"schema": "issue8406-schedule-harness-a01-v1",
            "fixture_sha256": hashlib.sha256(FIXTURE_PATH.read_bytes()).hexdigest(),
            "source_episode_ids": ids, "source_episode_sha256": digests,
            "query_dependencies": deps, "schedules": schedules}


def hostile_controls(raw, expected):
    outcomes = {}
    mutant = copy.deepcopy(raw)
    mutant["schedules"]["per_episode"]["updates"][0]["episode_refs"][0]["id"] = "forged-source-id"
    outcomes["forged_provenance"] = mutant != expected

    mutant = copy.deepcopy(raw)
    terminal = mutant["schedules"]["terminal"]["updates"][0]
    terminal["episode_refs"] = [ref for ref in terminal["episode_refs"]
                                if ref["id"] != "exception-protected"]
    outcomes["omit_rare_exception"] = mutant != expected

    mutant = copy.deepcopy(raw)
    row = next(r for r in mutant["schedules"]["per_episode"]["query_visibility"]
               if r["query_id"] == "contradictory" and r["checkpoint"] == 12)
    row["proposed_outcome"] = "SAFE"
    outcomes["collapse_conflict_as_safe"] = mutant != expected

    mutant = copy.deepcopy(raw)
    mutant["source_episode_sha256"]["safe-01"] = "0" * 64
    outcomes["mutate_episode"] = mutant != expected

    mutant = copy.deepcopy(raw)
    mutant["schedules"]["batch_4"]["updates"][0]["after_episode"] = 3
    outcomes["misalign_checkpoint"] = mutant != expected
    return outcomes


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: audit.py RAW.json AUDIT.json")
    fixture_bytes = FIXTURE_PATH.read_bytes()
    raw_bytes = Path(sys.argv[1]).read_bytes()
    errors = []
    if hashlib.sha256(fixture_bytes).hexdigest() != FIXTURE_SHA256:
        errors.append("fixture_hash")
    if hashlib.sha256(raw_bytes).hexdigest() != RAW_SHA256:
        errors.append("raw_hash")
    fixture, raw = json.loads(fixture_bytes), json.loads(raw_bytes)
    expected = reconstruct(fixture)
    if raw != expected:
        errors.append("independent_reconstruction")
    expected_counts = {"episodic_only": 0, "per_episode": 12,
                       "batch_4": 3, "terminal": 1}
    counts = {arm: {"updates": len(raw.get("schedules", {}).get(arm, {}).get("updates", [])),
                    "visibility_rows": len(raw.get("schedules", {}).get(arm, {}).get("query_visibility", []))}
              for arm in ARMS}
    if {arm: v["updates"] for arm, v in counts.items()} != expected_counts:
        errors.append("schedule_update_counts")
    if any(v["visibility_rows"] != 16 for v in counts.values()):
        errors.append("visibility_row_counts")
    controls = hostile_controls(raw, expected)
    if not all(controls.values()):
        errors.append("hostile_controls")
    result = {"status": "PASS" if not errors else "FAIL", "errors": errors,
              "disposition": "PASS_RETAINED_RAW_AUDIT_SCOPED" if not errors else "FAIL_RETAINED_RAW_AUDIT",
              "candidate_invocations_in_A02": 0, "auditor_invocations_in_A02": 1,
              "retries": 0, "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
              "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
              "source_episode_count": len(raw.get("source_episode_ids", [])),
              "schedule_counts": counts,
              "query_visibility_rows_total": sum(v["visibility_rows"] for v in counts.values()),
              "hostile_mutations_rejected": controls,
              "model_outputs": 0, "actions": 0, "task_effect_claims": 0}
    blob = (json.dumps(result, sort_keys=True, indent=2) + "\n").encode()
    fd = os.open(sys.argv[2], os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(blob)
    print(blob.decode(), end="")
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
