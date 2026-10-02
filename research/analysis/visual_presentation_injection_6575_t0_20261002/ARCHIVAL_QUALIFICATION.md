# Superseded T0 preparation archive qualification

Issue: [#6575](https://github.com/Unjuno/agent-interface/issues/6575)
Original branch: `research/visual-presentation-injection-6575-t0-20261002`
Original tip: `a2e40807fdcdd006159a66a32d8c9b9594d6a35b`.
Allocation: `VISUAL-PRESENTATION-INJECTION-6575-T0-20261002-01`.

This archive preserves a preparation package that was never assigned or run.
Its original `FREEZE.json`, source hashes, synthetic PPM inputs, runner and
tests remain unchanged. It is distinct from, and does not replace, the
consumed official T0 evidence in PR #6582.

## H/T/D/C/U

- **H — Hypothesis:** deterministic image transforms can preserve exact pixel
  provenance, target-region coverage and safety-region coverage while rejecting
  crops that hide required regions. This package does not test model response
  or prompt-injection susceptibility.
- **T — Treatment:** three synthetic PPM scenes, four presentation arms and
  six invalid-crop probes, with a proposed candidate/auditor sequence. No
  candidate or formal auditor was invoked.
- **D — Decision:** this branch is `SUPERSEDED_NO_RUN`; candidate=0,
  independent auditor=0, retries=0. The official Issue #6575 T0 in PR #6582
  remains `STOP_HARNESS_FIXTURE_MISMATCH` after six sham-crop provenance
  mismatches. This archive neither retries nor repairs that consumed outcome.
- **C — Controls:** the preparation record reports 3/3 host tests, two
  corruption controls, py_compile, and 13/13 frozen source SHA-256 values.
  The launcher failed closed because no exact #5085 assignment existed; no
  WSLc container or formal output was created. These are construction checks,
  not experimental findings.
- **U — Uncertainty:** the inputs are hand-annotated synthetic images. There
  is no semantic-legibility, model, GUI, user, task-effect, security, or
  susceptibility evidence. Any follow-up requires a distinct, explicitly
  authorized allocation after resolving the official STOP and resource gate.

The original preparation bytes are retained to aid review of the abandoned
source path. Do not launch this package as a retry or treat it as a second
result for the same T0 allocation.
