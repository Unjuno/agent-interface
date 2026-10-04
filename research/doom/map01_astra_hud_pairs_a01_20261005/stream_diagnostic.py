"""Join retained observation hashes to model-pending intervals without claiming semantics."""
from pathlib import PurePosixPath


def analyze(events, decisions, local_manifest, image_root_present):
    frames = local_manifest.get("frames", [])
    by_name = {PurePosixPath(row["file"]).name: row for row in frames}
    observations = sorted(
        (row for row in events if row.get("event") == "observation"),
        key=lambda row: row["capture_ns"],
    )
    mismatches = []
    seen_sequences = set()
    mapped = {}
    for row in observations:
        sequence = row.get("sequence")
        filename = PurePosixPath(row.get("image", "")).name
        if row.get("exact") is not True:
            mismatches.append({"kind":"nonexact_observation","sequence":sequence})
        if filename not in by_name:
            mismatches.append({"kind":"unmapped_image_path","sequence":sequence,"file":filename})
        else:
            mapped[id(row)] = by_name[filename]
        if sequence in seen_sequences:
            mismatches.append({"kind":"duplicate_sequence","sequence":sequence})
        seen_sequences.add(sequence)

    waits = []
    for index, decision in enumerate(decisions):
        start = decision["controller_model_started_ns"]
        end = decision["controller_model_ended_ns"]
        rows = [row for row in observations if start <= row["capture_ns"] <= end]
        before = [row for row in observations if row["capture_ns"] <= start]
        before_row = before[-1] if before else None
        prior_hash = mapped.get(id(before_row), {}).get("sha256") if before_row else None
        hashes = [mapped[id(row)]["sha256"] for row in rows if id(row) in mapped]
        changed = next((row for row in rows if id(row) in mapped and
                        mapped[id(row)]["sha256"] != prior_hash), None)
        gaps_ms = [(b["capture_ns"] - a["capture_ns"]) / 1e6
                   for a, b in zip(rows, rows[1:])]
        latest_sequence = rows[-1]["sequence"] if rows else None
        reported_sequence = decision.get("fresh_sequence_at_plan")
        sequence_match = (reported_sequence is None or reported_sequence == latest_sequence)
        if reported_sequence is not None and not sequence_match:
            mismatches.append({"kind":"return_sequence_mismatch","decision":index,
                               "reported":reported_sequence,"latest":latest_sequence})
        if not rows:
            mismatches.append({"kind":"no_observation_during_model_wait","decision":index})
        waits.append({
            "decision":index,
            "observation_count":len(rows),
            "first_sequence":rows[0]["sequence"] if rows else None,
            "latest_sequence":latest_sequence,
            "reported_fresh_sequence_at_plan":reported_sequence,
            "return_sequence_matches_latest_observation":sequence_match,
            "first_observation_latency_ms":((rows[0]["capture_ns"]-start)/1e6 if rows else None),
            "first_different_full_frame_hash_ms":((changed["capture_ns"]-start)/1e6 if changed else None),
            "unique_full_frame_hashes":len(set(hashes)),
            "max_capture_gap_ms":(max(gaps_ms) if gaps_ms else None),
        })

    per_wait_counts = [row["observation_count"] for row in waits]
    gaps = [row["max_capture_gap_ms"] for row in waits if row["max_capture_gap_ms"] is not None]
    novelty = [row["first_different_full_frame_hash_ms"] for row in waits
               if row["first_different_full_frame_hash_ms"] is not None]
    unique_paths = {PurePosixPath(row.get("image", "")).name for row in observations}
    return {
        "schema":"map01-astra-pending-observation-stream-a01",
        "disposition":"PASS_METADATA_ONLY" if not mismatches else "FAIL_METADATA_JOIN",
        "observation_count":len(observations),
        "exact_observation_count":sum(row.get("exact") is True for row in observations),
        "unique_sequence_count":len(seen_sequences),
        "unique_image_path_count":len(unique_paths),
        "manifest_frame_count":len(frames),
        "manifest_unique_sha_count":len({row["sha256"] for row in frames}),
        "unreferenced_manifest_frame_count":len(set(by_name)-unique_paths),
        "intermediate_image_bytes_present":bool(image_root_present),
        "model_wait_count":len(waits),
        "observation_count_per_wait":{"min":min(per_wait_counts),"max":max(per_wait_counts)},
        "max_internal_capture_gap_ms":{"max":(max(gaps) if gaps else None),"min":(min(gaps) if gaps else None)},
        "first_different_full_frame_hash_ms":{"min":(min(novelty) if novelty else None),"max":(max(novelty) if novelty else None)},
        "return_sequence_match_count":sum(row["return_sequence_matches_latest_observation"] for row in waits
                                           if row["reported_fresh_sequence_at_plan"] is not None),
        "return_sequence_reported_count":sum(row["reported_fresh_sequence_at_plan"] is not None for row in waits),
        "integrity_mismatches":len(mismatches),
        "mismatches":mismatches,
        "waits":waits,
        "interpretation":"event and hash-manifest metadata establish observation cadence and full-frame byte novelty only; missing frame bytes prevent ROI/content re-evaluation",
        "limits":[
            "full-frame SHA change does not establish material or semantic change",
            "the 419-entry manifest exposes hashes and sizes but intermediate PNG bytes are absent from this checkout",
            "no health-ROI response time, threat cause, safe action, task effect, recovery, physical release, or MAP01 success is established",
            "posthoc single-run metadata analysis, not a prospective allocation or preregistered experiment",
        ],
    }


if __name__ == "__main__":
    import hashlib
    import json
    from pathlib import Path

    here = Path(__file__).resolve().parent
    repo = here.parents[2]
    input_root = repo / "research/doom/results/map01-astra-attempt-v1"
    freeze = json.loads((here / "STREAM_FREEZE.json").read_text(encoding="utf-8"))
    for section in ("inputs", "code"):
        for relative, expected in freeze[section].items():
            digest = hashlib.sha256((repo / relative).read_bytes()).hexdigest()
            if digest != expected["sha256"]:
                raise SystemExit(f"FREEZE_HASH_MISMATCH {relative}")

    report = json.loads((input_root / "report.json").read_text(encoding="utf-8"))
    events = [json.loads(line) for line in (input_root / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    manifest = json.loads((input_root / "local-exact-frame-manifest.json").read_text(encoding="utf-8"))
    retained_root = repo / manifest["retained_location"]
    result = analyze(events, report["decisions"], manifest, retained_root.exists())
    result["base_main_sha"] = freeze["base_main_sha"]
    result["input_sha256"] = {relative: item["sha256"] for relative, item in freeze["inputs"].items()}
    (here / "STREAM_RESULT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "disposition": result["disposition"],
        "observation_count": result["observation_count"],
        "manifest_frame_count": result["manifest_frame_count"],
        "model_wait_count": result["model_wait_count"],
        "max_capture_gap_ms": result["max_internal_capture_gap_ms"]["max"],
        "intermediate_image_bytes_present": result["intermediate_image_bytes_present"],
        "integrity_mismatches": result["integrity_mismatches"],
    }, separators=(",", ":")))
