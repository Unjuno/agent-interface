# #1583 O3 generation-bound relevant-region gating — retained formal result

Task: `OBSERVATION-GATING-O3-RELEVANCE-GENERATION-20260918-001`

Decision: **`PASS_O3_GENERATION_BOUND_RELEVANCE_SCOPED`**.

## Question

O2 proves exact changed-tile transport and exact reconstruction, but O3 relevant-region gating adds a different safety dependency: the relevance declaration itself can become stale. This experiment isolates that freshness contract.

The candidate binds every relevance receipt to a runtime-owned relevance generation. Suppression is allowed only when the receipt is current and exact changed tiles are disjoint from both current relevant tiles and critical tiles. Missing, stale, wrong-scope or forged relevance fails open to `FORWARD_FULL_CURRENT`.

The negative comparator `STATIC_RELEVANCE` ignores relevance generation and continues using a historical region map.

## Construction

Directed construction passed before source freeze:

- current irrelevant change -> candidate suppresses;
- current relevant change -> candidate forwards;
- relevance A→B with stale A receipt and B-only change -> candidate `STALE_RELEVANCE_GENERATION` fallback, static comparator false-suppresses;
- fresh B receipt after A→B -> retired-A change suppresses again;
- critical tile outside ROI -> forwards;
- missing/wrong-scope/forged generation -> full-current fallback;
- malformed tile IDs, advance-before-init and conflicting receipt controls reject;
- exact duplicate receipt and same-relevance advance are no-ops.

Mandatory remote source readback found two preformal normalization-only differences: one extra candidate blank line and one unused local assignment `a=` in the runner. Remote canonical source removed both. Re-running excluded construction with the exact remote source produced the identical raw construction SHA-256 `968217ba84a980854e832b333416ed0a2e4d10a8345059011e02dfcf90224138`. Scientific logic, seed, corpus and gates were unchanged.

## Frozen formal

One deterministic formal invocation, seed `158020260918001`, reruns/replacements/tuning `0/0/0`.

| Family | Histories | Candidate result |
|---|---:|---|
| CURRENT_IRRELEVANT | 30,000 | suppressions 30,000 |
| CURRENT_RELEVANT | 30,000 | false suppressions 0 |
| SHIFT_STALE_HIDDEN | 40,000 | false suppressions 0; full-current fallback |
| FRESH_POST_SHIFT_IRRELEVANT | 30,000 | suppressions 30,000 |
| CRITICAL_OUTSIDE | 20,000 | false suppressions 0 |
| MISSING_RECEIPT | 20,000 | full-current fallback 20,000 |
| WRONG_SCOPE_RECEIPT | 15,000 | full-current fallback 15,000 |
| FUTURE_OR_FORGED_GENERATION | 15,000 | full-current fallback 15,000 |

Additional results:

- candidate/oracle full result+state mismatch: **0 / 200,000**;
- static stale comparator false suppressions in the shift discriminator: **40,000 / 40,000**;
- candidate stale hidden false suppressions: **0 / 40,000**;
- current relevant false suppressions: **0 / 30,000**;
- critical change false suppressions: **0 / 20,000**.

The key result is that generation binding fixes the stale-map escape without becoming permanently conservative: once a fresh g2 relevance receipt is installed, exact changes in the retired g1-only region can again be suppressed.

## Integrity

Frozen audit: PASS, errors `[]`; copied-result corruption controls 7/7 reject.

- formal result SHA-256: `dc63406b9ad52cf19c189eec13ac4762d8430ef5f5a31f64419592f460b77c7a`;
- retained compressed result SHA-256: `8a7f304379f0f6e156eb121121df3df877171d7e5fe0ea92a245426e97ba1e9c`;
- audit SHA-256: `5a2fcd6a1959e9eabcb184755ca2e7d237757aa1265a592c005fa846c869b99b`;
- deterministic ledger SHA-256: `ec56b81a4b7770d95a87461a2a091f1cc4c21da27d1d4b70b1ea17bcbc7858b7`.

Postformal source rehash matches the remote source freeze exactly.

## Interpretation

A relevant-region map is not durable authority. For O3-style suppression, a safe minimum contract is:

`exact changed tiles + current relevance receipt + current generation + critical override`.

Historical or unknown relevance should fall back to full/current evidence, not silently suppress.

This does not determine the right relevance region. A model or rule can still author an incorrect current region. Production may reuse a broader observation/currentness epoch instead of a dedicated relevance-generation field.

## Boundary

Synthetic relevance/currentness semantics only. No real GUI relevance distribution, model task quality, image-token reduction, latency, task success or production-runtime promotion claim. Existing O1/O2 results remain unchanged.
