# Issue #5841 T0 — frozen method construction

Status before computation: `PREREGISTERED / NOT_RUN`.

## H / T / D / C / U

**H.** In a finite matched two-route cohort with no true primary difference, route-specific missingness, a cross-cohort join, or an endpoint-export error can create a favorable primary-only contrast. A same-cohort sealed-identity / missingness / sentinel check should distinguish these from a clean null, a true primary-only benefit, scorer drift visible to a #5766-style reference deck, and an actual collateral sentinel mutation.

**T0.** Use exactly six deterministic no-model scenarios and four assigned episode IDs per route, with one expected negative-control row per assignment. Compute (1) a deliberately naive complete-case primary contrast, (2) pre/post reference-deck status, and (3) same-cohort assignment/join/missingness/sentinel coverage. Frozen scenarios: clean null; true primary benefit with unchanged sentinel; outcome-dependent guarded-route missingness; foreign-ID join contamination; endpoint-export misclassification also visible to the reference deck; and a real route-caused sentinel mutation. The independent oracle is a separate literal truth/decision table. Before the one-shot candidate run, run construction tests; then execute the candidate once, preserve its raw JSON, and invoke the separate raw-only auditor once. Mutations must reject a hidden negative-control row and a changed assignment identity.

**D.** `PASS_METHOD_SCOPED` only if (a) clean null and true primary benefit do not trigger a false ascertainment alarm; (b) missingness and foreign join are quarantined despite favorable complete-case contrasts; (c) reference-deck drift is distinguished from route-correlated missingness/join; (d) actual sentinel change is `COLLATERAL_FAIL`, never mere bias; and (e) the independent auditor reproduces the frozen six-case table and rejects both mutations. Otherwise `FAIL_METHOD` or `HOLD_INTEGRITY`. This does not establish that a chosen control is valid in a real GUI cohort.

**C.** Correct all-attempt accounting and an independent final-state oracle may already expose the same defects more simply. The reference-deck arm is expected to catch semantic scorer drift when the same check-standard path is exercised; it is not expected to detect a route-only missing row or a foreign task join. A passing negative control is not evidence that the primary endpoint is unbiased.

**U.** Small synthetic cases do not estimate sensitivity in a live benchmark. A sentinel can be affected by hidden shared UI state; route-caused changes are real collateral, not confounding. Endpoint-specific bias outside the sentinel's shared measurement path can escape. No product, causal-route, safety-rate, or human-use claim follows.

## Frozen expected outcomes (guarded minus direct)

| Scenario | Truth / fault | Naive complete-case primary delta | Reference deck | Same-cohort disposition |
|---|---|---:|---|---|
| `clean_null` | no route effect | 0.00 | PASS | `NO_CONTROL_SIGNAL` |
| `primary_benefit` | true primary-only benefit | +0.50 | PASS | `NO_CONTROL_SIGNAL` |
| `route_missingness` | same true outcomes; three guarded failures missing | +0.75 | PASS | `ASCERTAINMENT_HOLD` |
| `foreign_join` | no true route effect; guarded rows joined to foreign successes | +0.75 | PASS | `JOIN_INTEGRITY_HOLD` |
| `export_drift` | unchanged raw task state; guarded export mislabels endpoints | +0.50 | HOLD | `ORACLE_DRIFT_HOLD` |
| `real_collateral` | true primary benefit plus one actual guarded sentinel mutation | +0.50 | PASS | `COLLATERAL_FAIL` |

The numerical deltas are hand-derived from four assignments per route and are not estimates of any live effect. A nonzero primary-only delta is not itself promotion evidence.

## Constraints and publication

Pure offline Python computation on this Windows host; no network/model/provider, GUI, X11, game, GPU, or user input. Docker Desktop `desktop-linux` was checked read-only on 2026-10-01 with `docker version --format {{.Server.Version}}`; it did not respond within 4 seconds. No container command was issued. This is a host-only fallback, not the preferred container rung. Preserve complete assignment denominators and raw first outcomes. No retry or post-result tuning. If the result passes, publish the complete additive package in one GitHub branch commit and one draft PR; record the result on #5841 in the same delivery batch.
