# Issue #6500 — origin-to-effect binding method T0

## H / T / D / C / U

**H.** On a finite, independently specified metadata table, an origin-to-effect binding classifier has zero false accepts on wrong-origin, stale-generation, embedded-content, and wrong-recipient rows while accepting all legitimate fresh rows. It should reject more wrong-origin cases than visual-only and similarity-alarm comparators without blocking the legitimate controls.

**T.** Deterministic standard-library-only table with eight authored cases × three classifiers (`VISUAL_ONLY`, `SIMILARITY_ALARM`, `ORIGIN_BOUND`) = 24 rows. Fields include authorized origin, captured origin/generation, dispatch origin/generation, effect origin/recipient, intended recipient, pixel/label equivalence, similarity-risk score, and provenance completeness. One independent auditor reconstructs all decisions from raw fields without importing candidate code. Six mutation controls cover origin swap, generation staleness, similarity-score inversion, embedded-origin omission, target identity change, and recipient misbinding. No GUI, window, model, user data, or effect is used.

**D.** `PASS_METHOD_SCOPED` iff all 24 rows reconstruct exactly; the origin-bound arm allows both legitimate fresh controls, does not allow any of the six nonlegitimate rows, and returns `UNKNOWN` for the missing-provenance case; visual-only and similarity alarm each falsely allow at least one nonlegitimate lookalike; all six mutations are rejected. Otherwise `FAIL_METHOD`. This is a table/classifier method result only.

**C.** A trusted-window allowlist or fresh target handle may already reject most cases. Similarity alarms can be useful as an alarm, but they do not authenticate the receiving surface; origin metadata may still fail to identify hostile content inside an approved host.

**U.** Authored metadata cannot establish an OS provenance API's authenticity, race resistance, or completeness. No real spoofing, actual GUI action, security, safety, or product benefit is measured. In particular, a method PASS never grants user intent or action authority.

## Cases and frozen classifier contracts

Eight rows: two legitimate fresh controls (one with a high similarity-alarm score), low-risk-score pixel/label lookalike from another origin, reused stale generation, post-capture replacement before dispatch, missing process provenance, untrusted embedded content in an approved host, and wrong effect recipient within the otherwise approved app.

- `VISUAL_ONLY`: allow iff pixel/label match. It has no independent origin/freshness/recipient checks.
- `SIMILARITY_ALARM`: allow iff pixel/label match and frozen spoof-risk score `< 0.8`. This is an alarm threshold, not an identity proof.
- `ORIGIN_BOUND`: return `UNKNOWN` when provenance is incomplete or captured/current generation cannot be established; return `MISMATCH` for any known origin, dispatch, embedded-content, or effect-recipient mismatch; otherwise return `MATCH` only when authorized/captured/dispatch/effect origins, generation and intended/effect recipient all agree. `MATCH` is a scoped classifier result, not authorization.

Frozen allocation: `ORIGIN-EFFECT-BINDING-6500-ORB-T0-20261002-01`, 24 candidate rows, six mutation controls, candidate/auditor container counts 1/1, retries 0. Use locally cached digest-pinned image, OrbStack, pull never, network none, one CPU, 256 MiB, 64 PIDs, read-only root/source, separate output mounts. Any formal launch/audit failure consumes the allocation; no retry.
