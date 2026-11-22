# Recorded Win32 task effect R08

Status: `PASS_RECORDED_FIXTURE_EFFECT` after offline reconstruction from the
complete public call journal. The live call sequence itself finished and closed
normally; the first live runner stopped while constructing its canonical ledger
because it sent a normal-completion receipt through the recovery-only builder
branch. No call was replayed. The original runner, exact responses, and failure
are retained. The completed-owner handoff then reconstructed the run from those
raw bytes using the local adapter candidate and passed in normal and optimized
Python.

## Frozen conditions and live result

Conditions were frozen against main `7bcf4a795e71a466e004b066bfb48f0fcb2d5491`
under run ID `a1402ea90e1640048841adb7c45293b6`. One new visible Win32 fixture,
one `focus` + `A` + `release_all` action, one exact results lookup, two public
observations, six-second independent fixture effect, two-second late-input
horizon, and zero retries were used. Provider and model were `none`.

- The exact public action ID is `ce7b7aba8f414e5d9b868ea4b741d474`; its
  operation ID is `74744c5ac6264a2ba2870fd2bb9fa69d`.
- Before/after observation IDs are `a7967dd4688a4091abfaa31764b61799` and
  `e849cb4643bb497381f628569f96c58c`, on target generation
  `c9e0fdccc02ce26dcc51f2e5e51db645e34dcaec972037c71c33e557c640a64e`.
- Public action status was completed; verified neutral release was true. The
  two-second late-input horizon passed with 78 samples and a 32 ms maximum gap
  against the frozen 100 ms limit.
- The independent fixture observed exactly one accepted A key-down, key-up,
  and delayed text `a`. The score receipt reports factual and eligibility-aware
  task success true; the public runtime `task_success` field remains null.
- The independently timed effect interval is within authority. This action
  completed before lease expiry; this does not test an expired delayed action
  or recovery behavior.
- `interface_close` returned `closed`, with no unresolved public calls and
  replay denied. CUA no longer listed the fixture window and the exact fixture
  process PID exited.

## Adapter findings and local verification

The run exposed three real composition gaps: the standard observation
validator did not unwrap the public `review-v1` receipt while checking its
separate PNG block; the measured-run path did not project the standard program
from the hash-verified recorded `interface_dispatch` request; and the completed
effect handoff referenced an unbound `action_event`. These seams are repaired
in the implementation merged by PR #10451 at main
`7075902b6dd95da57a2e25819e2d2d6859239c25` in
`recorded_comparison_adapter_v1.py`,
`comparison_measurement_v1.py`, and `effect_receipt_handoff_v1.py`, with focused
tests. Five comparison/effect/owner suites pass **70/70 normally and 70/70 under
`-O`**. Normal and optimized offline R08 outputs are byte-identical; hashes are
in `raw/normal/` and `raw/optimized/`.

This is one no-provider fixture effect, not an efficiency comparison, recovery
trial, reliability estimate, MAP01 result, distributable-runtime acceptance,
or Research Preview graduation. The live action ran on the frozen main commit;
the merged adapters were used afterward to validate and reconstruct retained
evidence. PR #10451 integrates those repairs into main; the live fixture itself
was not rerun against the post-merge main.

## Custody

`conditions.json` is the immutable preregistration. `raw/` contains exact
public MCP envelopes and recorder bytes, both image artifacts, independent
fixture events/effect and score, window and foreground identity, close result,
excluded setup and reconciliation attempts, offline measured/adapted outputs,
and ordinary/optimized validation logs. `raw/SHA256SUMS.txt` covers every
retained raw file except the manifest itself. The original live runner remains
unchanged; `source/reconcile_recorded_run.py` is an offline-only reader and
adapter driver.

The complete project remains open on integrated efficiency, expiry/recovery
reliability, MAP01 task completion, supported-host acceptance and distributable
runtime criteria. See [the project state](../../../docs/PROJECT_STATE.md),
[the repository organization plan](../../../docs/REPOSITORY_ORGANIZATION_PLAN.md),
and [Issue #57](https://github.com/Unjuno/agent-interface/issues/57).
