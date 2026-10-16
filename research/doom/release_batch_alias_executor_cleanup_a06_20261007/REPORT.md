# A06 report: V13 cleanup after alias batch refusal

**Outcome: PASS_METHOD_SCOPED.** The frozen fake-X composition executed the current-main V13/V12/V5 executor with the V15/V2 release-batch backend and the V4/V3/V12 owner chain. A candidate-only duplicate-resolved-keycode guard rejected `up_batch(["a", "A"])` after both names had been admitted as keycode 38. The batch was published as incomplete with `step_exception`; V13 then called `release_all()` in its `finally` block and published a failed terminal with `release.verified=true`, `keys_down=[]`, `keys_unknown=[]`, and a successful KeyRelease/XSync/keymap receipt for code 38. Fake server state was empty after executor cleanup.

The frozen independent auditor passed all seven checks. Raw SHA-256: `d01a752df3e9739c17c6d2d9e87d9dba6356cc75fb7c472549388e4cf9601c28`. The package freezes main `decc1896e3e85ab2fdbb7ec4678f958eb6561d0f`. After execution, fetched main `133dafbd8f616b7d2f2ca8b14a3ba863b63f0933` and verified byte-for-byte that all 13 production source files used by this construction are unchanged there. The only behavioral guard is in the candidate-only V12 copy.

A04 and A05 are retained as STOP outcomes: A04's integrity precheck referenced a missing `sha()` helper; A05's frozen source closure omitted `executor_v5.py`. Neither reached setup or submitted input. A06 includes the expanded executor dependency closure and is a new one-shot, not a replay of either predecessor.

This shows the tested V13/V15 composition recovers an owned fake-server hold after the alias refusal. It does not show native X11, physical keyboard state, application response, Doom/MAP01 effect, a threat exposure, or live allocation. Issue #59's live gate remains unmet; this result is evidence to inform a future authorized live test, not a substitute for it.

Artifacts: `FREEZE.json`, `candidate.py`, `audit.py`, `results/A06_RAW.json`, `results/A06_AUDIT.json`, and predecessor STOP records under A04/A05.
