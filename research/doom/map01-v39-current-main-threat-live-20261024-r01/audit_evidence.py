"""Verify immutable provenance and summarize the bounded V39 attempts."""
import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def verify_prereg(path):
    record = load_json(path)
    digest_path = path.with_suffix(".sha256")
    expected = digest_path.read_text(encoding="ascii").split()[0]
    if sha256(path.read_bytes()) != expected:
        raise ValueError(f"prereg digest mismatch: {path}")
    commit = record["repository_commit"]
    pinned = record.get("runtime_source_sha256", record.get("source_sha256", {}))
    mismatches = []
    for name, expected_hash in pinned.items():
        if name.startswith("research/doom/map01-v39-current-main-threat-live-20261024-r01/"):
            source = (ROOT / name).read_bytes()
        else:
            source = subprocess.check_output(
                ["git", "show", f"{commit}:{name}"], cwd=ROOT
            )
        # The runtime checkout contains both LF and CRLF files under
        # core.autocrlf=true. Accept only the Git blob or its CRLF checkout.
        candidates = {sha256(source)}
        if b"\0" not in source:
            candidates.add(sha256(source.replace(b"\n", b"\r\n")))
        if expected_hash not in candidates:
            mismatches.append(name)
    return {"record": record, "source_hash_count": len(pinned),
            "source_hash_mismatches_against_commit": mismatches,
            "all_source_hashes_match_commit": not mismatches}


def summarize_r02(record):
    raw = ROOT / record["output"]
    runtime = raw / "runtime"
    events = [json.loads(line) for line in (runtime / "events.jsonl").read_text().splitlines()]
    owners = load_json(runtime / "owner-events.json")
    score = load_json(runtime / "score.json")
    scorer = load_json(runtime / "scorer-summary.json")
    observations = [event for event in events if event.get("event") == "typed_observation"]
    signals = {name: [event["signals"][name]["value"] for event in observations
                      if event.get("signals", {}).get(name, {}).get("status") == "observed"]
               for name in ("health", "ammo")}
    admissions = [event for event in events if event.get("event") == "input_admission"]
    explicit_up = [event for event in owners if event.get("event") == "owner_explicit_keyup"]
    releases = [event for event in owners if event.get("event") == "owner_release"]
    keyup_attempts = [attempt for event in releases
                      for key in event.get("key_release_attempts", {}).values()
                      for attempt in key.get("attempts", [])]
    return {
        "allocation_id": record["allocation_id"],
        "repository_commit": record["repository_commit"],
        "model": record["requested_model"],
        "effort": record["requested_effort"],
        "planner_turns_completed": sum(
            1 for line in (raw / "planner-protocol.jsonl").read_text().splitlines()
            if '"method":"turn/completed"' in line),
        "input_admissions": len(admissions),
        "completed_steps": sum(event.get("event") == "step_completed" for event in events),
        "explicit_keyups_server_verified": sum(event.get("server_keyup_verified") is True
                                                  for event in explicit_up),
        "release_batch_keyup_attempts": len(keyup_attempts),
        "release_batch_keyups_server_verified": sum(
            attempt.get("server_key_down_before") is True and
            attempt.get("server_key_down_after") is False and
            attempt.get("keyrelease_error") is None and attempt.get("sync_error") is None and
            attempt.get("keymap_after_error") is None
            for attempt in keyup_attempts),
        "all_owner_release_records_verified_empty": all(
            event.get("verified") is True and not event.get("keys_down") and
            not event.get("keys_unknown") and not event.get("key_state_errors")
            for event in releases),
        "health_observations": {"count": len(signals["health"]),
                                 "first": signals["health"][0], "last": signals["health"][-1],
                                 "unique": sorted(set(signals["health"]))},
        "ammo_observations": {"count": len(signals["ammo"]),
                               "first": signals["ammo"][0], "last": signals["ammo"][-1],
                               "unique": sorted(set(signals["ammo"]))},
        "independent_score": {key: score[key] for key in (
            "map", "map_exit", "player_dead", "death_count", "kill_count", "reward",
            "wall_control_ns")},
        "scorer_sample_count": scorer["sample_count"],
        "scorer_hz": scorer["scheduler"]["sample_hz"],
        "final_terminal_statuses": [
            {"id": event.get("id"), "status": event.get("status"),
             "steps_completed": event.get("steps_completed")}
            for event in events if event.get("event") == "terminal"],
        "limitations": [
            "one additive local WSL2 experiment; not a WSLc allocation",
            "not a MAP01 clear or reliability distribution",
            "X11 keymap evidence is not physical-key verification",
            "focus-query cancellation retired the observer; a later accepted step failed closed",
            "no matched efficiency comparison or human-tempo certification"],
    }


def main():
    prereg_paths = [BUNDLE / "PREREG.json",
                    BUNDLE / "diagnostics/session-stdout-probe-a02/DIAGNOSTIC_PREREG.json",
                    BUNDLE / "diagnostics/session-stdout-probe-a03/DIAGNOSTIC_PREREG.json",
                    ROOT / "research/doom/map01-v39-current-main-threat-live-20261024-r02/PREREG.json"]
    preregs = [verify_prereg(path) for path in prereg_paths]
    r02 = preregs[-1]["record"]
    if not preregs[2]["all_source_hashes_match_commit"] or not preregs[3]["all_source_hashes_match_commit"]:
        raise ValueError("current fix commit source hashes do not match the a03/r02 frozen records")
    result = summarize_r02(r02)
    result["a03_stdout_json_parse_failures"] = load_json(
        BUNDLE / "diagnostics/session-stdout-probe-a03/raw/result.json")["stdout_json_parse_failures"]
    result["prereg_digests_verified"] = len(preregs)
    result["source_hash_audit"] = [{
        "path": str(path.relative_to(ROOT)),
        "commit": entry["record"]["repository_commit"],
        "source_hash_count": entry["source_hash_count"],
        "all_source_hashes_match_commit": entry["all_source_hashes_match_commit"],
        "mismatches": entry["source_hash_mismatches_against_commit"]}
        for path, entry in zip(prereg_paths, preregs)]
    out = BUNDLE / "RESULT.json"
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    evidence_roots = [BUNDLE / "raw", BUNDLE / "diagnostics/session-stdout-probe-a02/raw",
                      BUNDLE / "diagnostics/session-stdout-probe-a03/raw",
                      ROOT / "research/doom/map01-v39-current-main-threat-live-20261024-r02/raw"]
    evidence_files = [file for base in evidence_roots for file in base.rglob("*") if file.is_file()]
    evidence_files += [BUNDLE / "PREREG.json", BUNDLE / "PREREG.sha256",
                       BUNDLE / "OUTCOME.md", BUNDLE / "audit_evidence.py"]
    evidence_files += [path for base in (BUNDLE / "diagnostics/session-stdout-probe-a02",
                                        BUNDLE / "diagnostics/session-stdout-probe-a03")
                       for path in (base / "DIAGNOSTIC_PREREG.json",
                                    base / "DIAGNOSTIC_PREREG.sha256", base / "probe_stdout.py")]
    evidence_files += [ROOT / "research/doom/map01-v39-current-main-threat-live-20261024-r02/PREREG.json",
                       ROOT / "research/doom/map01-v39-current-main-threat-live-20261024-r02/PREREG.sha256"]
    manifest = BUNDLE / "RAW_SHA256.jsonl"
    rows = [{"path": str(path.relative_to(ROOT)).replace("\\", "/"),
             "sha256": sha256(path.read_bytes()), "bytes": path.stat().st_size}
            for path in sorted(set(evidence_files))]
    manifest.write_text("".join(json.dumps(row, separators=(",", ":")) + "\n"
                                 for row in rows), encoding="utf-8")
    result["integrity_manifest"] = str(manifest.relative_to(ROOT)).replace("\\", "/")
    result["integrity_manifest_entries"] = len(rows)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
