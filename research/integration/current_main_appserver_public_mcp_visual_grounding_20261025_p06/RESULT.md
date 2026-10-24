# P06 outcome — completed visual grounding, pre-mint failure

The one preregistered Codex App Server turn completed against the exact public
Fake X observation and selected `[16, 8]`, the center of the green target. The
protocol usage receipt reports 10,185 input, 90 output, and 71 reasoning
tokens; the provider result reports a 6.23-second runner duration.

The run did **not** mint an action or dispatch input. The frozen runner raised
`KeyError('window_generation')` while preparing mint arguments. The public
observation contains `process_generation` and no `window_generation`; the
public caller therefore never reached the target-binding mint step. The raw
`run/RESULT.json` label is retained unchanged. The additive
`OUTCOME_CORRECTION.json` classifies this accurately as
`FAIL_AFTER_PROVIDER_PRE_MINT`.

`audit_failure_correction.py` verifies the correction against the provider
receipt, public observation and run SHA-256 manifest. The public-caller unit
checks also pass (3 tests). This establishes visual point selection in the
synthetic test only. It does not establish a public mint, input release, task
effect, bounded recovery, WSLc/live GUI transfer, MAP01, matched efficiency,
or reliability. P06 is consumed and was not retried.
