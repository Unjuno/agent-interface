# Issue #8397 T0 A01 report

**Disposition: `PASS_METHOD_SCOPED`.** The frozen candidate and independent
auditor each ran once (exit 0); the auditor reconstructed all five scenarios,
ten arms, and five preregistered discriminator checks with zero mismatches.
The pre-freeze seven-test suite passed, including rejection of all five
adversarial mutation controls.

The synthetic fixture showed one optional-observation interval before a
sensitive decision that preserved the authored exact effect while reducing
visible observations from 3 to 1 and payload bytes from 41 to 17. An interval
crossing a required transition reduced observations from 3 to 2 but changed
the effect from `target_saved` to `target_missed`. Post-completion captures
were invisible in both arms; captured-but-undelivered information was not
counted as model-visible; and an overlapping omission interval did not suppress
the mandatory safety cue or its safe-stop outcome.

Raw rows, individual checks, execution command/exit record, limits and hashes
are retained in this package. See [`RESULTS.md`](RESULTS.md) for the complete
arm table and interpretation, [`EXECUTION.md`](EXECUTION.md) for exact one-shot
invocations, and [`SHA256SUMS.txt`](SHA256SUMS.txt) for integrity checks.

This is a deterministic authored method fixture, executed with native Windows
CPython. It does not test the empirical hypothesis in Issue #8397 and does not
establish that observations may safely be omitted in a real GUI agent. No
runtime, GUI, model, game, OS input, container, WSL/WSLc, network, or GPU was
used.
