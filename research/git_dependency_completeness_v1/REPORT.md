# Real Git dependency-completeness discovery v1

## Decision

**RETAIN dependency completeness as a requirement separate from transaction atomicity.** An atomic effect can still be semantically stale if a relevant read dependency is omitted. Over-broad dependency sets can preserve safety but destroy valid concurrency.

Immutable source base: `21fb50be01e99816eb3a555e2ae131e679723f48`.

## Harness history

- a1: FAILED_HARNESS. The harness observed `terminal.json` existence before `write_text` completed and hit transient zero-byte JSON. No completed block promoted.
- a2: only change was wait-until-valid-JSON; completed 18/18 XTerm/XTEST rows.

## Rung 1 — omitted semantic dependency

Real Git 2.47.3 through XTerm/XTEST `./go`. Atomic transaction writes r1/r2 from expected A to B. Plan also semantically depends on `guard=A`, but guard is not written. `other` is unrelated.

After adapter check r1/r2/guard=A, harness changes guard→C or other→C. Both arms use one Git multi-ref transaction; only dependency predicate differs:

- `write_set_only`: transaction names r1/r2 only;
- `complete_dependency`: same transaction plus `verify guard A`.

3 blocks × 3 cases × 2 modes = **18 trials**.

| Case | write-set-only atomic transaction | atomic + guard verify |
|---|---:|---:|
| stable | correct B/B 3/3 | correct B/B 3/3 |
| guard A→C | **stale B/B commit 3/3** | **reject, A/A preserved 3/3** |
| unrelated other A→C | correct B/B + other C 3/3 | same 3/3 |

Thus atomicity over the write set does not imply semantic validity. The complete relevant read set must be in the effect predicate.

Measured effect section:
- write-set-only median 4.277 ms, range 3.603–4.782;
- complete dependency median 4.699 ms, range 2.596–5.967.
Frequency unpinned; descriptive only.

## Rung 2 — dependency precision frontier

After the GUI mechanism result, dependency-set declaration alone was varied in **900 direct Git transaction trials**: 100 repetitions × 3 worlds × 3 modes. Atomic r1/r2 write boundary stays fixed.

Modes:
- `write_only`: omit semantic guard;
- `exact_guard`: verify only relevant guard;
- `overbroad`: verify relevant guard and unrelated `other`.

| World | write-only | exact guard | over-broad |
|---|---:|---:|---:|
| stable | correct 100/100 | correct 100/100 | correct 100/100 |
| relevant guard A→C | **stale commit 100/100** | safe reject 100/100 | safe reject 100/100 |
| unrelated other A→C | correct progress 100/100 | correct progress 100/100 | **false reject 100/100** |

This yields the dependency precision frontier:
- under-declaration loses correctness;
- exact declaration preserves correctness and available concurrency in these seeded worlds;
- over-declaration preserves safety here but loses valid progress.

Timing medians: write-only 4.254 ms; exact 4.009 ms; over-broad 3.531 ms. These are not interpreted as a speed ranking because commit/reject work differs and large outliers exist. Primary outcome is correctness/selectivity.

Combined completed evidence: **918 rows** (18 XTerm + 900 dependency-set trials).

### Variable table

| Name | Meaning | SI unit | Definition | Type |
|---|---|---|---|---|
| r1,r2 | write set | 1 | expected A, planned B | identifiers |
| guard | relevant read dependency | 1 | plan assumes A; not written | identifier |
| other | unrelated resource | 1 | should not invalidate effect | identifier |
| effect interval | Git transaction duration | s | monotonic end-start | scalar |
| repetitions | trials per cell | 1 | 3 GUI; 100 direct | integer |

Unit check: ns intervals convert to ms by division by 1,000,000; refs/OIDs are identifiers.

## H / T / D / C / U

**H:** atomic compare-and-apply is semantically correct only if every relevant plan dependency is included; over-broad dependencies trade valid concurrency for unnecessary rejection.

**T:** 18 completed XTerm/XTEST rows after one retained harness failure; 900 direct Git dependency-set trials. Same atomic write transaction; only dependency declarations change.

**D:** PASS omission failure and exact-set protection: hidden guard change stale-commits 3/3 GUI and 100/100 direct when omitted, rejects 3/3 and 100/100 when included. Over-broad set falsely rejects unrelated changes 100/100.

**C:** the experiment uses a ground-truth dependency graph. It does not solve dependency discovery. An incorrect declared graph can still be wrong even with perfect transaction mechanics.

**U:** local Git, manually seeded dependencies, deterministic conflicts, no model/remote refs/production GUI. Evidence establishes mechanism and precision tradeoff, not automated dependency inference or natural rates.

## ERROR CHECK

Independent audits validate 18/18 GUI rows and 900/900 dependency-set rows. a1 is preserved as a harness failure and excluded from scientific claims.

## Architecture consequence

The candidate contract is now:

1. dependency evidence remains bound to the observation/plan that produced the action;
2. declare the complete **relevant** read set and non-partial write set;
3. enforce compare/verify + mutation in one effect-owner transaction;
4. avoid unrelated dependencies by default because they create false stops;
5. if a required dependency cannot be trusted/observed, yield/deopt/replan rather than infer semantic validity from visual stability.

The next open research problem is dependency discovery/authoring and calibration, directly related to Issue #93's footprint work.
