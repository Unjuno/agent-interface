# Issue #7678 manipulation sensitivity — four-route successor

This is successor A02 to the consumed three-route A01. The exact six true-order types, report masks, utility, #6274 source blobs, and one-shot candidate/auditor commands are in [`PREREGISTRATION.md`](PREREGISTRATION.md), [`fixture.json`](fixture.json), and [`FREEZE.json`](FREEZE.json).

**Disposition: `HOLD_AUDITOR_STARTUP_ERROR`; the D gate also fails on candidate control outputs.** A candidate invocation wrote 6,624 rows. Its one frozen formal auditor invocation failed before reconstruction because the dynamic loader omitted `__file__`. A separately versioned read-only audit reconstructed the matrix and exposed a candidate cache-key defect in the grant and protected-constraint controls. Neither formal process was retried; see [`RESULT.md`](results/a02/RESULT.md), [`RUN.json`](results/a02/RUN.json), and the preserved initial failure.

The diagnostic matrix shows frequent certificate changes but no safe-beneficial report under the selected best-route set utility and finite information partitions. This does not establish general strategyproofness or real-user behavior. It offers no basis for reducing transparency or changing the decision rule. Original A01 remains HOLD; its files and the prior #6274 result are untouched.
