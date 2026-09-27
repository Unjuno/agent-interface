# Issue #3066 v4 preparation status

**Disposition: `HOLD_PREFORMAL_OPENBOX_PRESS_WITNESS_MISSING`.** No v4 formal invocation occurred. The actual v4 runner was run construction-only against both declared cells. Bare reached the injected cleanup failure, exposed the typed `recovery_required=true` receipt, performed one supervisor release, and observed F8 up. Openbox stopped before the worker press was independently observed (`HOLD_KEY_PRESS_NOT_OBSERVED`; empty observer event log). The construction run is not a formal result and does not test the hypothesis in both configurations. No retry or post-construction tuning was performed.

One earlier construction command accidentally mounted the v3 experiment directory at `/exp`, invoking the v3 runner for its full 14-cell matrix. That raw output remains retained under `construction/02/` as construction-only incident evidence and was not used for v4 scoring. Correct v4 two-cell construction is retained under `construction/03/`.

The v4 runtime's ten source files are byte-identical to the fixed v3 source and to the same ten files in base main `c9bfb14c41b9ce72782a03ed4bfa0d814baf6a8f`; a later exact-main check at `22e9c43503109277073d7b2b667c354ef60bbba3` also confirmed the same bytes. Synthetic auditor tests passed (1 positive and 10 corruption controls). These checks do not compensate for the missing Openbox press witness.

The current main roadmap and Issues #57/#3311 prioritize integrated end-to-end efficiency after finalizing the active experiment. This v4 block is finalized as HOLD and remains open for future integration-blocker work; it must not be restarted until a concrete Openbox setup fix is independently justified.
