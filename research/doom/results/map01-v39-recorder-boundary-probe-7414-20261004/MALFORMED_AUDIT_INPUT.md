# Malformed auditor input probe — 2026-10-04

**H:** A malformed X11 keymap hex field in otherwise valid candidate evidence
could make the independent auditor raise rather than emit an explicit failed
or HOLD gate.

**T:** Replace an `after_admission` observer row's `keymap_hex` with
`not-hex`; run the source-level regression against pre-fix auditor commit
`eb11a9d05e05e0c078ab5ac151d47cc6f47644ba`, then against the repaired auditor.

**D:** The pre-fix evaluator raised `ValueError` from `bytes.fromhex()` during
the admission keymap check. The repaired evaluator returned
`FAIL_OR_HOLD_TELEMETRY_GATE`, with `audit_input_well_formed=false` and
`audit_error_type=ValueError`.

**C:** This was a deliberately malformed offline fixture; it does not imply
that retained live evidence contains malformed hex. A schema validator before
evaluation could also reject the input.

**U:** No X11 server, input, game, model, container, formal allocation, or real
candidate/raw record was used. This does not test event capture, physical
release, task feedback, recovery, matched comparison, or MAP01 outcome. The
auditor source change invalidates the old freeze's auditor hash; the consumed
T0 remains untouched.

The original probe report and exact source/test artifacts remain anchored at
the commits and paths listed in `SOURCE_PROVENANCE.md`.
