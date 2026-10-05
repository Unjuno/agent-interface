# V39/V15 post-batch keymap sampler A05 — retained STOP

The Issue #59 A05 preregistration called for three fresh FakeX cases: normal release, one deliberately missed key-up, and unavailable post-batch keymap sampling. The frozen candidate source started once against main `c1074c4dc385bae5b94ce93a5870e92c2e6ab07d`.

The normal case returned in memory. In the second case, the fake wrapper suppressed every `KeyRelease` for SPACE, including the owner cleanup attempt during `owner.close()`. The owner raised `RuntimeError: owner release not verified: [65]`; the third case did not run. The candidate runner writes its `RAW.json` only after all cases return, so neither the first case nor the partial second case was durably retained. `RUN_FAILURE.json` preserves the known failure and evidence gap.

Disposition: **STOP_FAKE_CLEANUP_DROP_ALIAS**. This is a harness defect and incomplete candidate execution, not a finding about production cleanup. The preregistration is one candidate and no retries; this candidate is consumed and must not be run again. A future successor can use a one-shot dropped-injection latch and persist each case as it completes, under a distinct freeze.

The read-only audit verifies the frozen source binding and STOP record only. It cannot reconstruct or independently audit the lost operation trace. This produces no conclusion about post-batch keymap attribution.
