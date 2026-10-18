"""Independent reconstruction and hostile-output audit; no candidate import."""
import copy
import hashlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURE_PATH = HERE.parent / "exception_preserving_skill_7418_t0_20261004" / "fixture.json"
FIXTURE_SHA256 = "1c8b74dfdd8ec7c5a5950133709ae95e40cc687edb12ac128d66f696c79e54fb"
PREFIXES = (3, 6, 9, 12)
ARM_NAMES = ("episodic_only", "per_episode", "batch_4", "terminal")


def stable_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def independently_reconstruct(fixture):
    rows = fixture["episodes"]
    sequence = [item["id"] for item in rows]
    digests = {item["id"]: hashlib.sha256(stable_bytes(item)).hexdigest() for item in rows}
    oracle = {item["id"]: item["source_episode_ids"] for item in fixture["applicability_oracle"]}
    deps = {"heldout-04": oracle["ordinary-skill"],
            "protected-heldout": oracle["protected-exception"],
            "contradictory": oracle["ambiguous-conflict"],
            "unrepresented": []}
    arms = {}
    schedule_points = {
        "episodic_only": [],
        "per_episode": list(range(1, len(sequence) + 1)),
        "batch_4": [n for n in range(1, len(sequence) + 1) if n % 4 == 0],
        "terminal": [len(sequence)]
    }
    for arm in ARM_NAMES:
        updates = []
        for n in schedule_points[arm]:
            updates.append({"after_episode": n,
                            "episode_refs": [{"id": episode_id, "sha256": digests[episode_id]}
                                             for episode_id in sequence[:n] ]})
        visibility = []
        for prefix in PREFIXES:
            due = [u for u in updates if u["after_episode"] <= prefix]
            if arm == "episodic_only":
                available = sequence[:prefix]
            elif due:
                available = [r["id"] for r in due[-1]["episode_refs"]]
            else:
                available = []
            last = due[-1]["after_episode"] if due else None
            for q, wanted in deps.items():
                found = [episode_id for episode_id in wanted if episode_id in available]
                state = ("NO_SOURCE_REQUIRED" if not wanted else
                         "FULL" if len(found) == len(wanted) else
                         "PARTIAL" if found else "NONE")
                visibility.append({"checkpoint": prefix, "latest_update_prefix": last,
                                   "query_id": q, "available_episode_ids": list(available),
                                   "required_source_ids": list(wanted),
                                   "retrieved_source_ids": found, "evidence_state": state})
        arms[arm] = {"updates": updates, "query_visibility": visibility}
    return {"schema": "issue8406-schedule-harness-a01-v1",
            "fixture_sha256": hashlib.sha256(FIXTURE_PATH.read_bytes()).hexdigest(),
            "source_episode_ids": sequence,
            "source_episode_sha256": digests,
            "query_dependencies": deps,
            "schedules": arms}


def acceptable(output, expected):
    return output == expected


def hostile_controls(raw, expected):
    cases = {}
    mutant = copy.deepcopy(raw)
    first_ref = mutant["schedules"]["per_episode"][0]["episode_refs"][0]
    first_ref["id"] = "forged-source-id"
    cases["forged_provenance"] = not acceptable(mutant, expected)

    mutant = copy.deepcopy(raw)
    terminal = mutant["schedules"]["terminal"]["updates"][0]
    terminal["episode_refs"] = [ref for ref in terminal["episode_refs"] if ref["id"] != "exception-protected"]
    cases["omit_rare_exception"] = not acceptable(mutant, expected)

    mutant = copy.deepcopy(raw)
    conflict_row = next(row for row in mutant["schedules"]["per_episode"]["query_visibility"]
                        if row["query_id"] == "contradictory" and row["checkpoint"] == 12)
    conflict_row["proposed_outcome"] = "SAFE"
    cases["collapse_conflict_as_safe"] = not acceptable(mutant, expected)

    mutant = copy.deepcopy(raw)
    mutant["source_episode_sha256"]["safe-01"] = "0" * 64
    cases["mutate_episode"] = not acceptable(mutant, expected)

    mutant = copy.deepcopy(raw)
    mutant["schedules"]["batch_4"]["updates"][0]["after_episode"] = 3
    cases["misalign_checkpoint"] = not acceptable(mutant, expected)
    return cases


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: audit.py RAW.json AUDIT.json")
    fixture_bytes = FIXTURE_PATH.read_bytes()
    if hashlib.sha256(fixture_bytes).hexdigest() != FIXTURE_SHA256:
        raise SystemExit("parent fixture hash mismatch")
    fixture = json.loads(fixture_bytes)
    expected = independently_reconstruct(fixture)
    raw_bytes = Path(sys.argv[1]).read_bytes()
    raw = json.loads(raw_bytes)
    errors = []
    if not acceptable(raw, expected):
        errors.append("raw_reconstruction")
    counts = {arm: {"updates": len(value["updates"]), "visibility_rows": len(value["query_visibility"])}
              for arm, value in raw.get("schedules", {}).items()}
    if len(raw.get("source_episode_ids", [])) != 12:
        errors.append("source_episode_count")
    if any(v["visibility_rows"] != 16 for v in counts.values()):
        errors.append("checkpoint_query_count")
    expected_updates = {"episodic_only": 0, "per_episode": 12, "batch_4": 3, "terminal": 1}
    if {arm: v["updates"] for arm, v in counts.items()} != expected_updates:
        errors.append("schedule_update_count")
    controls = hostile_controls(raw, expected)
    if not all(controls.values()):
        errors.append("hostile_control")
    result = {"status": "PASS" if not errors else "FAIL", "errors": errors,
              "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
              "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
              "source_episode_count": len(raw.get("source_episode_ids", [])),
              "schedule_counts": counts,
              "query_visibility_rows_total": sum(v["visibility_rows"] for v in counts.values()),
              "all_final_prefixes_have_same_source_ledger": len({
                  tuple(row["available_episode_ids"])
                  for arm in raw.get("schedules", {}).values()
                  for row in arm["query_visibility"] if row["checkpoint"] == 12
              }) == 1,
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
