# Formal result — Issue #4608

**Decision: HOLD — no material peak-allocation benefit.** The single frozen formal allocation completed on the pinned local Docker image without timeout or retry. All 24 resource workers and both contract workers completed. Correctness and contract checks passed; the auditor reported only the four pre-registered resource-benefit gate failures described below. No shared reader change is proposed.

## Frozen execution

- Main intake: `75b3d1e9cf1518ed7912670ea541fe969b2fb0cd`; study commit: `f66ba0c837c6423009af6cce2d010e7ee4db44b3`.
- Image: `python:3.13.5-slim-bookworm`, ID `sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419`; Docker Desktop local, network disabled, 5 CPU quota, 512 MiB, 64 PIDs, source read-only.
- Formal invocation count: exactly 1. Supervisor returned 0 in 6.14 seconds. No retry, tuning, seed/data replacement, or exclusions.
- Corpus: 4096 × 256 = 1,048,576 bytes; SHA-256 `cf1f260335c010a36382254c275b6b0776f9b792c202a518302d101e4a9d3f26`.
- `RAW.json` SHA-256 `901413b691952c1b3eb9b37996bf13ccf8fadb957f0cd9ffe5b2d58cd98fa518`.
- `PROGRESS.jsonl` SHA-256 `2578e3125fe15f680190b2f514f916f94a52bc0b2e2ff9cf273052f92b326b55`.
- `formal01.SUPERVISOR.json` SHA-256 `0fd581cc187d946844a750bc9a64fee31a2740d95e2990ab60d18bbb9d25d91d`.

## Independent audit and metrics

Raw-only auditor: 332 checks, with no receipt, cursor, exception, contract, source, environment, corpus, journal, or log-integrity errors. It reported four errors, all from the predeclared peak-benefit thresholds:

| Cursor records | Baseline peak bytes (3 reps) | memoryview peak bytes (3 reps) | Median peak ratio | Median wall ratio | Median CPU ratio |
|---:|---:|---:|---:|---:|---:|
| 0 | 1,089,443 / 1,088,954 / 1,089,348 | 1,082,976 / 1,082,976 / 1,082,881 | 0.9941 | 1.1914 | 0.9936 |
| 2048 | 1,575,585 / 1,575,585 / 1,575,585 | 1,575,585 / 1,575,585 / 1,575,585 | 1.0000 | 0.9648 | 0.9866 |
| 4064 | 2,091,681 / 2,091,681 / 2,091,681 | 2,091,681 / 2,091,681 / 2,091,681 | 1.0000 | 0.9765 | 0.9305 |
| 4096 | 1,055,745 / 1,055,745 / 1,055,745 | 1,055,745 / 1,055,745 / 1,055,745 | 1.0000 | 1.0551 | 1.0406 |

At both targeted long-prefix cursors (2048, 4064), candidate peak allocations were exactly equal to baseline in every repetition, failing both “lower in each match” and median ratio ≤0.75. Timing guards (≤1.20) passed. Accordingly this is a resource-efficacy HOLD, not a correctness failure. The small ~0.6% peak difference at cursor 0 is outside the targeted long-prefix gate and is not evidence for the stated hypothesis.

Corruption suite: 16/16 mutations rejected. Construction-only interruption test and STOP auditor had passed before formal. GPU/LoRA was not applicable to this CPU-traced allocation hypothesis; no GPU was used.

## Interpretation and next step

The current evidence does not support the claim that memoryview slices materially reduce traced peak allocation in this reader path. Keep the shared reader and predecessor record unchanged. Close this successor as HOLD after preserving the raw bundle. Any materially different profiling hypothesis should use a new successor issue and new pre-registered allocation; do not rerun this frozen case.

Limits remain those in `PLAN.md`: synthetic trusted fixed-width JSONL, one local CPython/OpenSSL build, three technical repetitions; `tracemalloc` does not measure native allocations, RSS, physical I/O, concurrency, other platforms, or end-to-end task behavior.
