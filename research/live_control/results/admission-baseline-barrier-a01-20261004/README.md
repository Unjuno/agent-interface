# Admission-time baseline barrier A01

This frozen construction experiment asks whether ExecutorV12's synchronous `accepted` emitter callback provides a same-thread baseline point after internal command admission and before the worker's first backend step, and whether a failure at that point leaves the executor in a recoverable lifecycle state.

Read [PLAN.md](PLAN.md) and [FREEZE.json](FREEZE.json) for H/T/D/C/U, source identities, run limits, and decision gates. The exact source-import closure is preserved under `source_snapshot/live_control/`. `candidate.py` is authorized for one execution; `audit.py` audits the saved result and negative controls. The experiment uses host Python because the prior OrbStack daemon preflight failure was not repeated. No game, X server, model, live input, or allocation is involved.

This package does not qualify a scorer reading a real game state or recovery task effect. A barrier-order pass with a failure-path STOP is not a runtime adoption PASS.
