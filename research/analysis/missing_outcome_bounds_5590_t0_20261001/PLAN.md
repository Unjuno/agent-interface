# #5590 T0 — finite-cohort missing-outcome bounds

## Question and H/T/D/C/U

- **H:** For a frozen benchmark cohort with unresolved terminal outcomes, the no-assumption finite-population success interval can prevent an observed-only promotion that is not identified by the retained ledger, while containing every compatible completion.
- **T:** On a fixed 10-episode ledger (6 verified success, 1 verified failure, 3 unresolved), compare observed-only, missing-as-failure, and sharp no-assumption bounds at a predeclared promotion threshold of 0.75. Exhaustively enumerate all `2^3` assignments of unresolved outcomes. A separate auditor independently recomputes the result from the ledger and rejects denominator/state/identity corruption.
- **D:** `PASS_BOUNDS_SCOPED` only if `N=S+F+M`, the independent implementation agrees on exact rational endpoints and the threshold disposition, every one of the eight compatible completions falls within the interval, both endpoints are attained, and corrupted denominators are rejected. `FAIL_INTEGRITY` on any mismatch. No empirical promotion result is inferred.
- **C:** If `M=0` or the threshold lies outside the bounds, this method need not change the decision; the interval still describes identification. A verified task contract may classify a missing terminal effect as failure, but that is a different preregistered taxonomy.
- **U:** Synthetic finite-cohort arithmetic only; no sampling-confidence interval, missingness model, population generalization, scorer validity, runtime safety, or benchmark promotion claim.

## Frozen source and allocation

- Issue: https://github.com/Unjuno/agent-interface/issues/5590
- Host T0 source base: `e32ace71fa1158ca8d5eec13fe620a1a51c1ff00`.
- A separate container rung must record its exact current-main SHA in its own formal execution manifest at the newly assigned start gate.
- Branch: `research/issue-5590-manski-sharp-bounds-t0-20261001`
- Additive path: this directory only.
- Allocation: `MANSKI-SHARP-MISSING-OUTCOME-5590-T0-20261001-01` (new slot required; prior AJ allocation T0-03 was consumed at preflight STOP and is not reused).
- Expected exact results: `N=10,S=6,F=1,M=3`; observed-only `6/7`; missing-as-failure `6/10`; identified interval `[6/10,9/10]`; threshold `3/4`; interval decision `PROMOTION_UNIDENTIFIED`; all 8 completions enumerated.

## Execution boundary

1. Run construction tests on host; these test code paths and corruptions but do not invoke the formal candidate or claim the Docker result.
2. Freeze this directory and hash manifest.
3. At a newly assigned OrbStack slot, revalidate main, full queue, source hashes, cached image digest/platform, and active container inventory. No pull/build/network.
4. Invoke the candidate once in a network-disabled container with read-only source and a distinct writable output mount. If it exits zero, invoke the raw-only auditor once in a separate container with only the frozen ledger, raw output, and auditor mounted read-only. No retry.
5. Preserve candidate/audit stdout, stderr, exit statuses, commands, image/source identities and hashes. Infrastructure/provenance failures are STOP, not scientific FAIL.

The previous allocation `COMPETING-RISK-AJ-CENSORING-5590-T0-20261001-03` remains a separate consumed preflight STOP and is not modified.
