# Typed final action-admission receipt

The v31 live allocation exposes a boundary race that planner eligibility alone
cannot describe. A planner answer may already be completed and protocol-eligible
when a hard policy event is handled before controller action admission. The
controller correctly discards that answer, but downstream analysis needs an
explicit final admission state.

`final_action_admission_v1.py` defines a model-free one-way receipt:

- any observed authority-reducing policy invalidation wins before admission,
  regardless of whether it arrived before or after planner terminal;
- an interrupted, failed, or ineligible planner turn is rejected;
- a clean completed planner answer becomes
  `READY_FOR_FRESH_EXECUTOR_ADMISSION`, which still grants no input;
- only a later exact Executor `accepted` event records `INPUT_ADMITTED`;
- a subsequent hard event records `REVOKED_POLICY_INVALIDATED` while preserving
  the historical executor acceptance rather than rewriting it.

Each transition checks monotonic boundary order. Malformed invalidations,
future-dated evidence, authority-granting invalidation records, duplicate
admission, and admission from a rejected receipt fail closed. Receipt builders
record evidence and do not issue input themselves.

Seven tests pass on Windows and WSL/Linux. They cover hard-before-terminal,
terminal-before-hard-before-admission, clean completion plus later executor
acceptance, typed terminal/controller-validation no-input, admission-before-
later-hard revocation, malformed evidence, and the exact retained v31 decision0 race. In that real trace, planner status is
completed/eligible and interrupt returns `already_terminal`, but the typed final
result is `REJECTED_POLICY_INVALIDATED`, matching the controller's zero-plan
admission.

V32 now integrates the receipt into its model, controller-validation, terminal,
policy-rejection and active-plan paths and binds READY to the first accepted
primary program. Live behavior remains untested; see
`research/doom/MAP01_FINAL_ADMISSION_V32.md`.

The deterministic six-path record is retained at
`results/final-action-admission-paths-v1/audit.json`. Windows and Linux produce
the same bytes and verify zero/one acceptance cardinality plus post-admission
revocation history.
