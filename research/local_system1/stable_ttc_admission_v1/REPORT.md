# Stable TTC admission result

Decision: **`PASS_STABLE_TTC_ADMISSION_SCOPED`**

Formal: 4 fresh seeds, one invocation per seed, reruns/replacements/tuning 0.

## Frozen factor

Exact #906 TTC training/data/model/confidence semantics were retained. Only intermediate action admission changed: `DIRECT_TTC` externalizes the first executable action above confidence 0.90; `STABLE_TTC` requires the same executable action above the unchanged gate on two adjacent stages. Final-stage termination is unchanged.

## First outcome

| seed | stress premature direct | stress premature stable | stable stress accuracy | stable ordinary compute | stable stress compute | mean latency reduction vs full | p50 reduction | p95 regression |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 9081701 | 4/4096 | 0/4096 | 0.989502 | 0.763245 | 0.850586 | 17.70% | 15.62% | -2.37% |
| 9081702 | 4/4096 | 0/4096 | 0.989502 | 0.767761 | 0.856384 | 22.80% | 17.60% | -17.76% |
| 9081703 | 4/4096 | 2/4096 | 0.988281 | 0.769104 | 0.856628 | 18.71% | 13.47% | -8.51% |
| 9081704 | 5/4096 | 0/4096 | 0.985596 | 0.772644 | 0.857727 | 17.39% | 14.18% | -3.12% |

Aggregate stress premature executable: **17 -> 2**.
Paired median mean latency reduction vs FULL_DEPTH: **18.21%**; median p50 reduction: **14.90%**; candidate mean faster pairs: **4/4**.
All four candidate p95 ratios were below FULL_DEPTH; every frozen gate passed. Independent frozen auditor recomputed the aggregate decision with errors `[]`. Copied-evidence corruption controls rejected 6/6 mutations.

## Interpretation

A two-stage stability requirement materially reduced premature executable externalization on this synthetic progressive-evidence task without changing the confidence threshold or retraining objective. The tradeoff is deliberate: candidate normalized compute rises relative to direct TTC because the earliest possible exit moves one stage later. The result supports *stability-gated early externalization* at this scoped synthetic boundary; it does not establish real GUI action safety.

## Limits / stop

- Synthetic 4-stage progressive evidence, one CPU/PyTorch environment and four seeds only.
- Adjacent agreement can repeat the same wrong action; it is not semantic verification.
- No screenshot perception, GUI task, provider/model API, task input or authority path is tested.
- Timing is local batch-1 CPU inference; no human-tempo or end-to-end computer-use claim follows.
- Do not tune the 0.90 confidence gate, confirmation length, data noise/signal or training epochs from this allocation.

## Integrity

- FREEZE SHA-256 `14bdf6df19ec34fd26c14b0d5fc06c4673d0803f3b404411e47d72e63ba7f6a3`
- source archive SHA-256 `99df3f4ef578ff083cac1058f26eed7d974848dbd9edaaaefa6e1e263fd0502e`
- FORMAL_RESULT SHA-256 `2b60a2f139a5ef603ee6c6c4114629fcb04f379c0de573347cc4bd5d2deb2387`
- AUDIT SHA-256 `eb5dec33b5ffeaa9e818d45a610d628dad6eccb6043b535ec46f0b5a03d104b0`
- POSTFORMAL SHA-256 `0fee315b6b3d3eb2700d4d6e0f7643aa42ddd05e88c3465771561ab40150acf0`
- CORRUPTION_CONTROLS SHA-256 `d3238a3617be35a7d5f349a6853a84c3f715d5b2a31adc7cbd47d293bdc6fb61`
