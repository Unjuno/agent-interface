# Bounded interval temporal-reversal estimator under ±1% localization jitter

Issue: #1311  
Task: `TEMPORAL-REVERSAL-BOUNDED-INTERVAL-R1-20260918-006`  
Decision: **PASS_BOUNDED_INTERVAL_JITTER_RECOVERY_SCOPED**

Formal discipline: one invocation, zero reruns/replacements/tuning. 2400/2400 paired estimator rows completed. Independent audit reported no errors; four corruption controls were rejected; source hashes after formal exactly match the preformal freeze.

| reversal age | STRICT_EXACT | BOUNDED_INTERVAL | candidate UNKNOWN | candidate wrong | noiseless ceiling |
|---:|---:|---:|---:|---:|---:|
|25 ms|0.000|0.240|0.760|0.000|0.250|
|50 ms|0.000|0.495|0.505|0.000|0.500|
|75 ms|0.000|0.740|0.260|0.000|0.750|
|100 ms|0.000|0.995|0.005|0.000|1.000|
|150 ms|0.000|1.000|0.000|0.000|1.000|
|200 ms|0.000|0.985|0.015|0.000|1.000|

The only scientific factor is the estimator. The paired traces retain 10 Hz cadence, unit-speed one-reversal motion, 500 ms history and deterministic independent per-sample localization jitter bounded to ±0.001 position units. The candidate uses the known resulting ±0.002 displacement-error bound, at most three newest samples and fail-closed `UNKNOWN` when the sampled history does not establish a reversal.

This recovers 96–100% of the favorable noiseless identifiability ceiling at every measured age while producing zero wrong-direction outputs. It does **not** establish real visual localization error bounds, acceleration robustness, multi-reversal behavior, GUI/task correctness, production latency, human tempo or runtime promotion.

The raw 2400-row `FORMAL_RESULT.json` is deterministic from the frozen source and task seed. Run `RECONSTRUCT.py` as an audit reconstruction (not a new scientific allocation); it regenerates the bytes and checks the retained SHA-256.

Artifact SHA-256:
- `FORMAL_RESULT.json`: `7f337e5ed0e13bb392985ac80f9c5b7fe6e2b2a0994e773d6454b5ab9de7182d`
- `AUDIT.json`: `c6531defcb3aa097783522024b5fb43d66109e73890ac8d579a8fa1116a21290`
- `CORRUPTION.json`: `9fa3c8393b5289def80e9efabcba005ed10b6457414dbf9e2e307c21480d1715`
