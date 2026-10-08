#!/usr/bin/env python3
"""Issue #8654 C04 finite candidate; writes and fsyncs raw JSONL before audit."""
import argparse
import hashlib
import itertools
import json
import math
import os
import sys
from pathlib import Path

N = 16
P_ALT = 0.25
REGIMES = {
    "STABLE": (1.0, 0.0),
    "REVERSAL": (0.0, 1.0),
    "GLOBAL_SHIFT": (0.0, -1.0),
}

def binomial_probability(k):
    return math.comb(N, k) * (P_ALT ** k) * ((1.0 - P_ALT) ** (N - k))

def classify(cue_mean, contrast, complete_support):
    if not complete_support:
        return "UNIDENTIFIABLE"
    if contrast < 0.0:
        return "REVERSAL"
    if cue_mean > 0.5:
        return "STABLE"
    return "GLOBAL_SHIFT"

def diagnostic_row(regime, outcomes, k0, k1):
    cue_outcome, alternative_outcome = outcomes
    cue_count = (N - k0) + (N - k1)
    alternative_count = k0 + k1
    cue_sum = cue_count * cue_outcome
    alternative_sum = alternative_count * alternative_outcome
    cue_mean = (cue_sum / (1.0 - P_ALT)) / (2 * N)
    alternative_mean = (alternative_sum / P_ALT) / (2 * N)
    contrast = cue_mean - alternative_mean
    complete_support = 0 < k0 < N and 0 < k1 < N
    return {
        "arm": "DIAGNOSTIC",
        "regime": regime,
        "k0_alt": k0,
        "k1_alt": k1,
        "probability": binomial_probability(k0) * binomial_probability(k1),
        "cue_count": cue_count,
        "alternative_count": alternative_count,
        "cue_reward_sum": cue_sum,
        "alternative_reward_sum": alternative_sum,
        "complete_support": complete_support,
        "cue_mean_ht": cue_mean,
        "alternative_mean_ht": alternative_mean,
        "contrast_ht": contrast,
        "decision": classify(cue_mean, contrast, complete_support),
    }

def greedy_row(regime, outcomes):
    cue_outcome, _alternative_outcome = outcomes
    return {
        "arm": "GREEDY_CUE_ONLY",
        "regime": regime,
        "k0_alt": 0,
        "k1_alt": 0,
        "probability": 1.0,
        "cue_count": 2 * N,
        "alternative_count": 0,
        "cue_reward_sum": 2 * N * cue_outcome,
        "alternative_reward_sum": 0.0,
        "complete_support": False,
        "cue_mean_ht": None,
        "alternative_mean_ht": None,
        "contrast_ht": None,
        "decision": "UNIDENTIFIABLE",
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()
    args.raw.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for regime, outcomes in REGIMES.items():
        for k0, k1 in itertools.product(range(N + 1), repeat=2):
            rows.append(diagnostic_row(regime, outcomes, k0, k1))
        rows.append(greedy_row(regime, outcomes))

    digest = hashlib.sha256()
    byte_count = 0
    with args.raw.open("xb") as stream:
        for row in rows:
            data = (json.dumps(row, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")
            stream.write(data)
            digest.update(data)
            byte_count += len(data)
        stream.flush()
        os.fsync(stream.fileno())
    dir_fd = os.open(str(args.raw.parent), os.O_RDONLY)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)

    receipt = {
        "allocation": "8654-C04",
        "candidate_invocations": 1,
        "rows_written": len(rows),
        "raw_path": args.raw.as_posix(),
        "raw_bytes": byte_count,
        "raw_sha256": digest.hexdigest(),
        "file_and_parent_directory_fsynced": True,
        "source_commit": os.environ.get("GITHUB_SHA", "LOCAL_PREFLIGHT_ONLY"),
        "python": sys.version,
    }
    with args.receipt.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    receipt_dir_fd = os.open(str(args.receipt.parent), os.O_RDONLY)
    try:
        os.fsync(receipt_dir_fd)
    finally:
        os.close(receipt_dir_fd)
    print(json.dumps(receipt, sort_keys=True))

if __name__ == "__main__":
    main()
