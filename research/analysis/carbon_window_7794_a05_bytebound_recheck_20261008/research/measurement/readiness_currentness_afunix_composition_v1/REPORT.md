# Readiness/currentness AF_UNIX composition — first formal outcome

Decision: **PASS_READINESS_CURRENTNESS_AFUNIX_COMPOSITION_SCOPED**.

This is the one source-first formal invocation for Issue #1372. Reruns/replacements/tuning: **0**. The candidate extends the exact #1179 current-evidence record by only `readiness_generation:uint64` and `readiness_state:uint8`; total fixed record size is **66 bytes**.

## Formal result

- matched records: **240,000**;
- candidate/oracle mismatches: **0**;
- exact AF_UNIX record-identity mismatches: **0**;
- readiness-only nonready effects: **0**;
- ABA old-generation effects: **0**;
- fresh post-transition READY effects: **20,000**;
- normal READY effects: **120,000**;
- HARD effects: **0**;
- AMBIGUOUS effects: **0**;
- readiness authority promotions: **0**;
- deliberately unsafe CURRENTNESS_ONLY stale-readiness effects: **60,000**.

## Timing

Persistent AF_UNIX acquisition + validation over 240,000 measured reads:

- p50: **0.019593 ms**;
- p95: **0.043766 ms** (gate <=1.0 ms);
- p99: **0.132650 ms** (gate <=2.0 ms);
- max: **6.532828 ms**;
- median socket-minus-inproc: **0.018175 ms** (gate <=0.50 ms).

In-process validation p50/p95/p99: **0.001414/0.002230/0.002352 ms**.

## Integrity

Independent audit: PASS/errors[]. Five copied-result corruption controls reject. Postformal source SHA-256 recheck matches the frozen source set exactly. Formal result SHA-256: `0482dc4a82eba067acb7cb3a6ce52fc1335b875e1afbc266007fa5542d9229f5`. Raw timing-vector commitment: `687427f7857fa4f6f84a62d699529496bbad1be3baeb5a4f39c1e5e8332ca6a1`.

## Scope

Synthetic/local-IPC composition only. This does **not** establish model quality, real application readiness, X11/task correctness, human tempo, or a production ABI. The result supports carrying readiness generation/state in the same high-frequency final guard rather than treating historical READY as permission.
