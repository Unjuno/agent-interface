#!/usr/bin/env python3
"""Read-only supplemental replay from the committed gzip artifact.

This is post-hoc artifact/reconstruction validation, not another formal
candidate or frozen-auditor invocation. It never writes candidate.json or
overwrites audit.json/audit.stdout.json.
"""
import gzip
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import audit as frozen

ROOT = Path(__file__).resolve().parent
FORMAL = ROOT / "formal_01"
OUT = FORMAL / "replay_validation.json"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_stream(stream):
    digest = hashlib.sha256()
    while chunk := stream.read(1024 * 1024):
        digest.update(chunk)
    return digest.hexdigest()


def main():
    if OUT.exists():
        raise SystemExit("STOP_REPLAY_VALIDATION_OUTPUT_EXISTS")
    freeze = read_json(ROOT / "FREEZE.json")
    receipt = read_json(FORMAL / "candidate.stdout.json")
    compressed = FORMAL / "candidate.json.gz"
    expected_raw_sha256 = "afaf783f1f8f8e5f7c4ee93661e27f8962a0c883456650531278de901bd3135f"
    expected_gzip_sha256 = "b391bc0edb3799a6ad0badf7b9f2abe23457b55d13277dc51b477b7abdd6cdb7"

    compressed_sha256 = frozen.sha(compressed)
    if compressed_sha256 != expected_gzip_sha256:
        raise SystemExit("STOP_COMPRESSED_ARTIFACT_HASH_MISMATCH")
    with gzip.open(compressed, "rb") as stream:
        candidate_sha256 = sha256_stream(stream)
    if candidate_sha256 != expected_raw_sha256:
        raise SystemExit("STOP_COMPRESSED_CANDIDATE_HASH_MISMATCH")
    if receipt["candidate_sha256"] != freeze["source_sha256"]["candidate.py"]:
        raise SystemExit("STOP_CANDIDATE_SOURCE_RECEIPT_MISMATCH")

    # Parse directly from gzip; do not materialize or overwrite the 300 MB raw file.
    with gzip.open(compressed, "rt", encoding="utf-8") as stream:
        payload = json.load(stream)
    source_hashes_match = all(
        frozen.sha(ROOT / name) == expected
        for name, expected in freeze["source_sha256"].items()
    )
    if not source_hashes_match:
        raise SystemExit("STOP_FROZEN_SOURCE_HASH_MISMATCH")

    training, public, oracle = (
        read_json(ROOT / name) for name in ("training.json", "public.json", "oracle.json")
    )
    errors, rows, transcript = frozen.verify(
        payload, training, public, oracle, freeze["input_sha256"]
    )
    if errors:
        raise SystemExit("SUPPLEMENTAL_RECONSTRUCTION_ERRORS:" + ",".join(errors))

    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["cohort"], row["checkpoint_cost"], row["replay_cost"])].append(row)
    cell_summary = []
    informative_benefit_all_cells = True
    incomplete_reversed_rows = 0
    for (cohort, checkpoint_cost, replay_cost), group in sorted(grouped.items()):
        candidate = [row["total_cost"] for row in group]
        fixed = [row["fixed"]["total_cost"] for row in group]
        event = [row["event"]["total_cost"] for row in group]
        med_candidate = frozen.statistics.median(candidate)
        med_fixed = frozen.statistics.median(fixed)
        med_event = frozen.statistics.median(event)
        complete = all(row["completed"] and row["final_effects"] == row["expected_effects"]
                       for row in group)
        if cohort == "informative":
            gain_fixed = (med_fixed - med_candidate) / med_fixed if med_fixed else 0.0
            gain_event = (med_event - med_candidate) / med_event if med_event else 0.0
            informative_benefit_all_cells &= gain_fixed >= 0.10 and gain_event >= 0.10
        else:
            gain_fixed = (med_fixed - med_candidate) / med_fixed if med_fixed else 0.0
            gain_event = (med_event - med_candidate) / med_event if med_event else 0.0
        if cohort == "reversed":
            incomplete_reversed_rows += sum(
                not row["completed"] or row["final_effects"] != row["expected_effects"]
                for row in group
            )
        cell_summary.append({
            "cohort": cohort,
            "checkpoint_cost": checkpoint_cost,
            "replay_cost": replay_cost,
            "n_episode_cost_rows": len(group),
            "all_exact_complete": complete,
            "median_candidate": med_candidate,
            "median_fixed": med_fixed,
            "median_event": med_event,
            "reduction_vs_fixed": gain_fixed,
            "reduction_vs_event": gain_event,
        })

    prior_audit = read_json(FORMAL / "audit.json")
    result = {
        "format": "7466-a03-posthoc-readonly-replay-v1",
        "classification": "supplemental artifact/reconstruction validation; not a formal allocation invocation",
        "candidate_invocations_added": 0,
        "frozen_auditor_invocations_added": 0,
        "compressed_candidate_sha256": candidate_sha256,
        "compressed_artifact_sha256": compressed_sha256,
        "source_hashes_match_freeze": source_hashes_match,
        "candidate_rows_reconstructed": len(rows),
        "streamed_ticks_reconstructed": len(transcript),
        "reconstruction_errors": errors,
        "prior_formal_mutations_rejected": prior_audit["mutations_rejected"],
        "informative_benefit_all_cells": informative_benefit_all_cells,
        "incomplete_reversed_episode_cost_rows": incomplete_reversed_rows,
        "distinct_reversed_episode_ids": len({row["episode_id"] for row in rows
                                               if row["cohort"] == "reversed"}),
        "formal_disposition_unchanged": prior_audit["disposition"],
        "legacy_clairvoyant_lower_bound": "withdrawn: frozen DP allowed zero-work idle transitions",
        "summary": cell_summary,
    }
    OUT.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
                   encoding="utf-8")
    print(json.dumps({key: result[key] for key in (
        "classification", "candidate_rows_reconstructed", "streamed_ticks_reconstructed",
        "reconstruction_errors", "informative_benefit_all_cells",
        "incomplete_reversed_episode_cost_rows", "distinct_reversed_episode_ids",
        "formal_disposition_unchanged", "legacy_clairvoyant_lower_bound",
    )}, sort_keys=True))


if __name__ == "__main__":
    main()
