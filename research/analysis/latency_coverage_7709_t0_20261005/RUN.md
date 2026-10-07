# T0 execution receipt

- Date: 2026-10-05 (Asia/Tokyo environment date).
- Frozen main: `c837ad535eed085d95744ad0a9680535a5bb7143`.
- Freeze-time branch: `research/7709-t0-segment-coverage-20261005`, observed identical to frozen main before execution. During publication its ref became unavailable to the GitHub ref API; it was not force-updated or deleted by this task.
- Intermediate package branch: `research/7709-t0-coverage-delivery-20261005`, created additively from the package commit on the frozen-main lineage.
- Final review branch: `research/7709-t0-expanded-stress-20261005`, based on the then-current main after the contemporaneous #7709 T0 and T1 results appeared.
- Runtime: Ubuntu on WSL2, CPython 3.12.3, host CPU; not a WSLc/Docker/container run, as Issue #7709 T0 explicitly does not require one.
- Formal invocation order/counts: generator 1, candidate 1, independent auditor 1; retries 0.
- Generator exited 0 and reported 1,152,000 paired windows.
- Candidate exited 0 and produced 4,000 result rows.
- Auditor exited 0: `PASS_METHOD_SCOPED`; scoped directional result `SUPPORTED_SCOPED`; exact raw reconstruction of 1,152,000 windows; all three frozen mutation controls rejected.
- No model, GPU, GUI, live app, input, network, or external side effect.
- Resource observation before execution: `memory.max=max`, `cpu.max=max 100000`, `pids.max=max`; WSL reported 4.2 GiB available and 2 GiB swap (15 MiB used). These are host values, not container or per-process enforcement.

## Commands

```text
python3 generate.py CONFIG.json INPUT.jsonl
python3 candidate.py INPUT.jsonl CANDIDATE.jsonl CONFIG.json
python3 audit.py INPUT.jsonl CANDIDATE.jsonl CONFIG.json AUDIT.json
```

All commands ran from this frozen package directory in the Ubuntu WSL distro. `INPUT.jsonl` was created only after the freeze. Raw candidate and audit artifacts are retained without editing.

## Output identities

| Artifact | Rows / bytes | SHA-256 |
|---|---:|---|
| `INPUT.jsonl` | 4,000 / 29,285,304 | `0d8937064f8fe2567f6d571c60eb0b326eec04bc585d8a33a559c26666bf9f23` |
| `CANDIDATE.jsonl` | 4,000 / 2,555,408 | `376ac068feca10c6bf34796ebe87342baed62c31ebdf583b642dfb901156f159` |
| `AUDIT.json` | 4,663 bytes | `9cd151bada033ea20a2daebabe38f96aed940c135ab74358df2abdd1827f44c6` |
| `INPUT.jsonl.gz` | 12,137,705 | `433b425e12a7ee2b6db1bd572af7e97790d8e8d0ccea025e5601764411142af3` |
| `CANDIDATE.jsonl.gz` | 472,798 | `738c3a17a8e7cb90eafa2f5293801f0d312729a3cea41e36b602282b0742f686` |

The gzip archives were tested, then decompressed hashes matched the original raw files exactly. The candidate has one output record per input replicate. The auditor independently reconstructed every record from raw input and checked exact row/censor denominators, detected boundaries, confidence intervals, interval coverage, false-promotion counts, and boundary perturbations.

## Concurrent #7709 result distinction

While this frozen run was underway, another worker merged PR #7729 with a related #7709 T0. That prior result used three workloads, 240 all-null datasets/workload, 8 sessions × 40 trials, four fixed temporal blocks, and 5% censoring. This run was independently frozen earlier against main `c837ad5` and differs materially: four workload families including warm-up and a nonzero effect, 8- and 16-session cells, 500 replicates/cell, 24 windows/session, 10% censoring, a data-driven descriptive split rule, and explicit missed/extra-boundary invariance tests. It is an expanded stress variant, not a replacement or rerun of PR #7729. Its largest added caution is that the detector over-segments stationary-null data; the interval gain itself comes from session-level replication, not segmentation. The later #7709 T1 `HOLD_TOO_FEW_INDEPENDENT_RUNS` remains unchanged and neither T0 supports real-route claims or authorizes T2.
