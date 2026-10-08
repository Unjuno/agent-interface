#!/usr/bin/env python3
"""Read-only corrected clairvoyant diagnostic for Issue #8283.

Consumes the immutable Issue #7466 A03 inputs and compressed candidate receipt.
It never imports/invokes candidate or frozen-auditor drivers and never writes
into the predecessor package.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
PRED = REPO / "research/analysis/hazard_checkpoint_7466_feedback_gate_a03_20261004"
OUT = ROOT / "RESULT.json"
EXPECTED_RAW = "afaf783f1f8f8e5f7c4ee93661e27f8962a0c883456650531278de901bd3135f"
EXPECTED_GZIP = "b391bc0edb3799a6ad0badf7b9f2abe23457b55d13277dc51b477b7abdd6cdb7"


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def iter_candidate_episode_rows(path: Path):
    """Decode only the top-level episodes array; never load the large transcript."""
    decoder = json.JSONDecoder()
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        buffer = ""
        position = 0
        eof = False

        def fill():
            nonlocal buffer, position, eof
            if position:
                buffer = buffer[position:]
                position = 0
            chunk = stream.read(1024 * 1024)
            if chunk:
                buffer += chunk
            else:
                eof = True

        def whitespace():
            nonlocal position
            while True:
                while position < len(buffer) and buffer[position].isspace():
                    position += 1
                if position < len(buffer) or eof:
                    return
                fill()

        def value():
            nonlocal position
            while True:
                whitespace()
                try:
                    parsed, end = decoder.raw_decode(buffer, position)
                    position = end
                    return parsed
                except json.JSONDecodeError:
                    if eof:
                        raise
                    fill()

        whitespace()
        if buffer[position] != "{":
            raise ValueError("candidate root is not an object")
        position += 1
        while True:
            whitespace()
            if buffer[position] == "}":
                return
            key = value()
            whitespace()
            if buffer[position] != ":":
                raise ValueError("malformed candidate object")
            position += 1
            if key != "episodes":
                value()
                whitespace()
                if buffer[position] == ",":
                    position += 1
                    continue
                return
            whitespace()
            if buffer[position] != "[":
                raise ValueError("candidate episodes is not an array")
            position += 1
            while True:
                whitespace()
                if buffer[position] == "]":
                    return
                yield value()
                whitespace()
                if buffer[position] == ",":
                    position += 1
                elif buffer[position] == "]":
                    return
                else:
                    raise ValueError("malformed candidate episodes array")


def constrained_oracle(case, interruptions, cp_cost, replay_cost):
    """DP over (progress,durable); every transition advances exactly one tick.

    At tick t, choose no checkpoint or a checkpoint iff legal[t] and
    progress > durable; then perform one unit of work and apply interruption[t].
    """
    states = {(0, 0): 0}
    best_complete = None
    for tick, interrupted in enumerate(interruptions):
        following = {}
        for (progress, durable), cost in states.items():
            choices = (False, True) if case["legal"][tick] and progress > durable else (False,)
            for checkpoint in choices:
                next_durable = progress if checkpoint else durable
                next_cost = cost + (cp_cost if checkpoint else 0)
                next_progress = progress + 1
                if interrupted and next_progress < case["task_units"]:
                    next_cost += (next_progress - next_durable) * replay_cost
                    next_progress = next_durable
                if next_progress >= case["task_units"]:
                    best_complete = next_cost if best_complete is None else min(best_complete, next_cost)
                    continue
                key = (next_progress, next_durable)
                following[key] = min(following.get(key, float("inf")), next_cost)
        # For equal progress, a state with at least as much durable work and
        # no greater accumulated cost dominates every lower-durable state.
        grouped = defaultdict(list)
        for (progress, durable), cost in following.items():
            grouped[progress].append((durable, cost))
        states = {}
        for progress, frontier in grouped.items():
            cheapest = float("inf")
            for durable, cost in sorted(frontier, reverse=True):
                if cost < cheapest:
                    states[(progress, durable)] = cost
                    cheapest = cost
    return best_complete


def self_test():
    case = {"task_units": 2, "legal": [1, 1, 1, 1]}
    assert constrained_oracle(case, [0, 0], 3, 1) == 0
    assert constrained_oracle(case, [1, 0, 0], 3, 1) == 1
    assert constrained_oracle(case, [1, 1, 0, 0], 3, 1) == 2
    case = {"task_units": 2, "legal": [0, 1, 1]}
    assert constrained_oracle(case, [1, 0, 0], 3, 2) == 2


def main():
    if OUT.exists():
        raise SystemExit("STOP_RESULT_ALREADY_EXISTS")
    self_test()
    freeze = read_json(PRED / "FREEZE.json")
    public = read_json(PRED / "public.json")
    oracle = read_json(PRED / "oracle.json")
    receipt = read_json(PRED / "formal_01/candidate.stdout.json")
    raw_hash = hashlib.sha256()
    with gzip.open(PRED / "formal_01/candidate.json.gz", "rb") as stream:
        while chunk := stream.read(1024 * 1024):
            raw_hash.update(chunk)
    gzip_hash = sha_bytes((PRED / "formal_01/candidate.json.gz").read_bytes())
    if gzip_hash != EXPECTED_GZIP or raw_hash.hexdigest() != EXPECTED_RAW:
        raise SystemExit("STOP_CANDIDATE_ARTIFACT_HASH_MISMATCH")
    if receipt["candidate_sha256"] != freeze["source_sha256"]["candidate.py"]:
        raise SystemExit("STOP_SOURCE_RECEIPT_MISMATCH")
    if receipt["episodes"] != 432:
        raise SystemExit("STOP_FORMAL_ROW_RECEIPT_MISMATCH")
    by_id = {item["episode_id"]: item for item in oracle["episodes"]}
    public_by_id = {item["episode_id"]: item for item in public["episodes"]}
    expected_n = len(public["episodes"]) * len(public["checkpoint_costs"]) * len(public["replay_costs"])
    results = []
    for row in iter_candidate_episode_rows(PRED / "formal_01/candidate.json.gz"):
        case, hidden = public_by_id.get(row["episode_id"]), by_id.get(row["episode_id"])
        if case is None or hidden is None:
            raise SystemExit("STOP_EPISODE_JOIN")
        optimum = constrained_oracle(case, hidden["interruptions"],
                                     row["checkpoint_cost"], row["replay_cost"])
        if optimum is None or optimum <= 0 or optimum > row["total_cost"]:
            raise SystemExit("STOP_ORACLE_OR_GAP_INVARIANT")
        results.append({"episode_id": row["episode_id"], "cohort": hidden["cohort"],
            "checkpoint_cost": row["checkpoint_cost"], "replay_cost": row["replay_cost"],
            "candidate_cost": row["total_cost"], "corrected_oracle_cost": optimum,
            "gap": row["total_cost"] - optimum})
    if len(results) != expected_n or expected_n != 432:
        raise SystemExit("STOP_EPISODE_COST_CARDINALITY")
    cells = defaultdict(list)
    for row in results:
        cells[(row["cohort"], row["checkpoint_cost"], row["replay_cost"])].append(row)
    summary = []
    for (cohort, cp, replay), group in sorted(cells.items()):
        gaps = [item["gap"] for item in group]
        opts = [item["corrected_oracle_cost"] for item in group]
        summary.append({"cohort": cohort, "checkpoint_cost": cp, "replay_cost": replay,
            "n": len(group), "oracle_cost_min": min(opts),
            "oracle_cost_median": statistics.median(opts), "oracle_cost_max": max(opts),
            "gap_min": min(gaps), "gap_median": statistics.median(gaps),
            "gap_max": max(gaps), "zero_gap_rows": sum(gap == 0 for gap in gaps)})
    result = {"format": "7466-a03-corrected-clairvoyant-diagnostic-a01",
        "issue": 8283, "predecessor_issue": 7466,
        "classification": "read-only post-hoc diagnostic; not candidate/auditor invocation",
        "candidate_invocations_added": 0, "frozen_auditor_invocations_added": 0,
        "a03_disposition_changed": False,
        "a03_formal_disposition": read_json(PRED / "formal_01/audit.json")["disposition"],
        "compressed_candidate_sha256": gzip_hash, "decompressed_candidate_sha256": raw_hash.hexdigest(),
        "candidate_rows_reconstructed": len(results), "hand_fixture_checks": 4,
        "all_oracle_costs_strictly_positive": all(r["corrected_oracle_cost"] > 0 for r in results),
        "all_candidate_minus_oracle_gaps_nonnegative": all(r["gap"] >= 0 for r in results),
        "summary": summary, "rows": results,
        "limits": ["synthetic schedules and stipulated costs only",
            "clairvoyant comparator is unattainable and diagnostic only",
            "does not explain or repair A03 safety/completion or benefit failures"]}
    OUT.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("classification", "candidate_rows_reconstructed",
        "hand_fixture_checks", "all_oracle_costs_strictly_positive",
        "all_candidate_minus_oracle_gaps_nonnegative", "a03_disposition_changed")}, sort_keys=True))


if __name__ == "__main__":
    main()
