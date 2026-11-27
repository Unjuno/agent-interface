# Preregistration: typed-health early-dispatch input-occupancy comparison

**Question / Issue:** #59 — when a typed health signal is already available while the image artifact is still pending, does handling it immediately reduce held-input occupancy compared with waiting the retained artifact-ready lag?

**H:** Immediate typed monitoring should reduce key-down→verified-owner-release by approximately the injected artifact-ready delay, while both arms produce the same `HARD_INVALIDATED`, cancel-before-planner-interrupt ordering, verified empty release, and ineligible pending answer.

**T (fixed):** Use the exact V39 helper functions, PR #8866 monitor blob, Executor V13, input transition owner V4 → V3 → V12, and in-memory fake X from the synthetic tree. Admit health-only guard from health 97 (effective hard minimum 89); hold keycode 65; deliver typed health 40 at sequence 2. Early arm calls monitor immediately. Delayed arm waits exactly 150.031473 ms before delivering the identical typed event, matching the maximum `typed_emit_to_artifact_ready_ms` among the retained 218 observations in `inputs/source-report.json`. Measure from fake backend key-down to owner `verified_ns`.

**D (fixed before collection):** Ten paired runs, alternating arm order by pair (early→delayed for odd pairs, delayed→early for even pairs). Success requires every run to preserve the hard invalidation, verified empty keys/buttons, no input authority, and pending-answer ineligibility; median paired held-time reduction ≥ 140 ms; all ten pairwise reductions > 0. Retain first failure and stop; do not retry or replace it. This is a local construction comparison, not a live allocation.

**C (fixed):** Source snapshot is synthetic stack commit `b6f0cc68adc1c67d6b1c878b7d9ce1af6abe3152`; PR #8866 monitor file must match its recorded Git blob. Runtime image is local immutable digest `python@sha256:b9767f56a1cc620aa72d38cc3557d26412e38a4597c92953476136b78894ccbd`, with 1 CPU, 512 MiB memory, no network, unprivileged user, no GPU. Each run uses a fresh `--rm` container. Source bind is read-only; only result bind is writable.

**U (scope):** Wait injection is controlled and derived from one retained trace. Fake X is in-memory; this cannot establish real OS/GUI/game event delivery, a causal survival benefit, useful task feedback, recovery, or actual physical key occupancy. The 10 pairs characterize this integration under the selected runtime only. WSLc may warn that swap limits are unsupported; report observed cgroup files if available and do not infer complete enforcement from flags.

Pilot smoke runs at 111.11915 ms and zero delay are preserved separately in `smoke/` and excluded from the ten registered pairs. The delay was selected from the complete retained 218-event array before formal pair collection.
