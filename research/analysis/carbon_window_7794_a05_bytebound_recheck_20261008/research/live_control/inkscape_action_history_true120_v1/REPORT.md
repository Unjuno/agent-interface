# Corrected true-120 ms Inkscape action-history boundary

Task `INKSCAPE-ACTION-HISTORY-TRUE120-20260916-001`, correction Issue #509.

## Decision

**`NO_INCREMENTAL_HISTORY_AT_TRUE_120MS`**.

Merged PR #498 remains retained historical evidence, but its timing interpretation was wrong: its eight self-switch rows sampled the guard only 3.265–4.336 microseconds after `Tab.end`, because the 120 ms deadline was anchored before an expensive revalidation scoring step. This allocation changes only that scheduling boundary.

## Frozen correction

The same Inkscape 1.4 two-red-rectangle fixture, A-selection predicate, `Tab`, A-handle guard, two policies, Right x5 effect, persisted-SVG scorer and terminal input-release checks are retained. The repaired runner records `revalidation_complete_ns` after the predicate finishes. Stable rows sample the guard 120 ms after that point. Self-switch rows emit one controller-authored `Tab` and sample the guard 120 ms after `Tab.end_ns`. Formal timing gate was [120,150] ms.

Construction was excluded. Exact source hashes and 16-case schedule were published to GitHub before measurement. No formal ID was rerun, replaced or extended.

## First formal outcome

- stable + current guard: 4/4 `ADMIT`, guard 64/176/64, A +10 / B 0;
- stable + history invalidation: 4/4 `ADMIT`, guard 64/176/64, A +10 / B 0;
- self-switch + current guard: 4/4 `DEPENDENCY_UNAVAILABLE`, guard 0/0/0, zero Right input, A 0 / B 0;
- self-switch + history invalidation: 4/4 `DEPENDENCY_UNAVAILABLE`, guard 0/0/0, zero Right input, A 0 / B 0.

Actual anchor-to-guard interval across all16 rows: min 120.036 ms, median 120.569 ms, max 120.938 ms. Frozen auditor: errors 0.

Therefore the self-action receipt adds **no incremental correctness at the true 120 ms boundary in this fixture**: by then the current visual guard already reflects the changed selection and both policies fail closed. This does not negate the narrower #498 near-immediate result. It corrects its causal scope.

## Supporting verification

A postformal independent checker re-decoded all 16 guard ROIs, recomputed dark-pixel counts and RGB hashes, checked receipt/anchor ordering and 120–150 ms timing, recomputed SVG deltas, and rechecked terminal input release: PASS, errors0. Four copied-evidence corruptions (timing claim, guard claim, SVG delta claim, receipt order) were rejected 4/4. This postformal checker supports but does not alter the frozen decision.

## Limits

One Inkscape 1.4/X11 fixture and one self-authored selection-navigation action. No natural race-rate, external/unreceipted change detection, AT-SPI identity, model benefit, arbitrary GUI or product claim. A different action/theme/backend may have a different paint-publication interval.

## Successor

Do **not** pursue external/unreceipted selection change using the old assumption that the guard is still aliased after 120 ms. Any successor should first identify an independently retained condition where current observation remains insufficient at the actual consumption boundary, then test a distinct evidence source.

## ERROR CHECK

16 distinct formal IDs, four rows per stratum, no reruns/replacements, all [120,150] ms timing gates pass, stable controls8/8 correct, switch current guard unavailable8/8 across both policies, release checks16/16, frozen audit errors0.
