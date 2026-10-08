# Issue #59 — strict paired-binding identity and timestamp order (A05 construction)

## H / T / D / C / U

**H.** A04 checks that each health/ammo pair shares one epoch, but must also reject a later sequence whose capture timestamp regresses and must compare nested binding values with exact JSON types. A sequence increase alone does not prove a newer frame; Python equality aliases `True` and `1` inside dictionaries.

**T.** Added regressions for a pair at `(sequence=12, capture_ns=1_200_000_000)` followed by `(13, 1_150_000_000)`, source and current-frame bindings differing only by nested `focus: true` versus `focus: 1`, then reran the paired monitor, existing V39, source-refresh, and immediate action-validity suites. The same three regressions were first run against frozen A04 controller source `26318c8209590b95fcc3eb9aff0b534efeb55a05`; captured output is `baseline-red.txt`.

**D.** PASS only if the A04 baseline fails the timestamp and nested-binding regressions, the repaired current code passes all focused regressions, both changed Python files compile, and `git diff --check` passes.

**C.** The source-binding alias could be admitted because the pair matcher used Python equality; the per-signal guards independently compare canonical JSON, so a current-only alias could still invalidate later. The fix rejects aliases at the paired boundary before those guards run. Regressions use synthetic observations and readers.

**U.** This verifies local fail-closed construction semantics only. It does not establish live producer behavior, temporal latency, controller cancellation timing, physical key release, verified empty input, useful task effect, or MAP01 progress. No game, GUI, model, OS input, container, or formal allocation was run.
