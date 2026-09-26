# Issue #4261 formal result

Allocation: `runtime-assurance-fallback-4261-20260923-01`.

Decision: **PASS_RUNTIME_ASSURANCE_FALLBACK_SCOPED**.

## Hypothesis and test

The frozen candidate runtime-assurance monitor should route unsafe or stale learned-control actions to a verified fallback, while preserving nominal operation and yielding safely when fallback is unavailable. The formal allocation covered 16 held-out deterministic scenarios and two policies (baseline and candidate), for 32 rows total, with 14 efficacy scenarios. It ran exactly once using the frozen command `python3 runner.py --out formal-01 --formal`.

## Result

The candidate had 0 violating ticks versus 67 for baseline, and 82 safe-progress ticks versus 45. Stale retakes were 0. The audit reported no errors. All six corruption controls were rejected: candidate violation, stale retake, false release, unavailable fallback, removed row, and erased baseline violations. The runner exited 0 and emitted 32 formal rows.

## Scope and limitations

This is a deterministic synthetic 1-D plant result. The monitor observes current drift, and fallback uses `u=-sign(x)`. It does not validate learned-model quality, a real GUI, MAP01, end-to-end latency, model-provider behavior, or general fallback safety. Treat the result as scoped evidence for this fixture only.

The frozen environment requested CPython 3.13.5 and standard-library SQLite on Linux x86_64. The container used CPython 3.13.5, SQLite 3.40.1, and x86_64, but its observed WSL2 kernel/glibc string differs from the historical freeze metadata (Linux 6.18.44/glibc 2.41 vs Linux 6.6.114.1 WSL2/glibc 2.36). No network, GUI input, or model provider was used.

## Integrity and execution

The frozen source archive SHA-256 is `7d636abda7d875f2377ee5245103fab450fa3c16dc594dec511a112fe4678da4`. All nine source members matched FREEZE.json before execution. The raw result SHA-256 is `b375624ea5f40835f98b0eecd4c968ff8f24ba5143777554baea3cbcd8a0a548`. Container prestart/result receipts, environment, runner streams, execution record, raw rows, audit, and controls are retained alongside this report. The run had one invocation, no retry, no replacement, no tuning, and no formal/construction overlap.
