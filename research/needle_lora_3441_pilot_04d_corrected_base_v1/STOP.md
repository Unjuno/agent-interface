# Formal STOP — Issue #4471

Disposition: `STOP_FORMAL_RESULT_SERIALIZATION_NAMEERROR_AFTER_TRAINING`.

The single formal local RTX 3080 invocation exited 1 on 2026-09-26 UTC. Training fit loops and all six held-out row-scoring calls precede the failure in the frozen runner. Result-dictionary construction then referenced the removed symbol `STEPS` at line 201, raising `NameError: name 'STEPS' is not defined`.

The process had computed the fit/evaluation objects in memory but emitted no stdout JSON (0 bytes); it did not persist model state or row predictions. Thus there is no recoverable metric result and no scientific PASS/FAIL/HOLD. The frozen control flow implies 400 base updates plus four 120-update adapter fits (880 optimizer-step calls), but per-step receipts were not retained.

Exact captured stderr: 723 bytes, SHA-256 `26dde93146e5d032aa9339daf04964d2e1a391190ee4a8fdd6459f8935d3f87e`, losslessly retained as `FORMAL_STDERR.raw.b64`. Empty stdout SHA-256 is `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.

No retry, source edit followed by execution, tuning, or result reconstruction was performed. The allocation is consumed. The issue, preregistration, source freeze, preflight and all predecessor outcomes remain distinct and unchanged.
