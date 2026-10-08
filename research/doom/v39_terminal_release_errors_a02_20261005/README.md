# V12 terminal-release send and state-sampling failures A02

This post-hoc local regression package extends the release-receipt repair proposed in PR #8025. It covers a second failure boundary: a KeyRelease send exception must not prevent later key releases, server-state sampling, or retention of an unverified `owner_release` receipt. The existing keymap-sampling failure regression from A01 remains in the same suite and remains unchanged in its frozen formal record.

## H / T / D / C / U

- **H:** On the exact V12 owner source proposed here, a KeyRelease send exception leaves a typed, unverified receipt attached to the raised error, later keys still receive release attempts, and a subsequent explicit release can verify empty state. Pointer/keymap sampling failures also retain the receipt and unknown state.
- **T:** Freeze the ten-file import/test closure and current-main baseline source. Run the new send-failure case against baseline and require the missing-receipt failure; then run the four adjacent owner/transition suites against the candidate, requiring 24 passing tests and successful compilation.
- **D:** PASS this local regression gate only when the baseline case fails for the expected missing receipt, candidate tests report 24/24 and `OK`, compilation exits 0, and the independent audit verifies every source and result hash. Otherwise retain the output as a stop or failure.
- **C:** The fake X server is deterministic and exercises the real V12 owner thread plus V3/V4 transition wrappers. It cannot model X server transport uncertainty, shared-display races, physical keys, or application consumption.
- **U:** No real X server, GUI, game, model, OS input, formal allocation, physical release, latency bound, recovery efficacy, threat response, task effect, or MAP01 completion is established.

The package freeze occurs after the test and implementation were developed and before the retained reproduction run. It is post-hoc regression evidence, not preregistration of a formal experiment. PR #8025's original `STOP_AUDIT_RAW_TRACE_MISSING` record remains preserved; this package does not rerun its candidate or auditor allocation.

Run `python -B run_verification.py` from this directory with the bundled Python runtime. The runner first verifies the expected baseline failure in a disposable overlay, then runs the candidate suites and compile check in a separate overlay. `audit.py` independently checks the pinned source snapshots and captured outputs.
